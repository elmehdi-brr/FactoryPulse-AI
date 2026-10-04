from httpx import AsyncClient


async def create_base_hierarchy(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> dict[str, int]:
    organization_response = await client.post(
        "/organizations",
        headers=admin_headers,
        json={
            "name": "Test Industries",
            "code": "TEST-ORG",
            "description": "Automated test organization",
        },
    )
    assert organization_response.status_code == 201
    organization = organization_response.json()

    site_response = await client.post(
        "/sites",
        headers=admin_headers,
        json={
            "organization_id": organization["id"],
            "name": "Test Factory",
            "code": "TEST-SITE",
            "location": "Test Location",
            "description": "Automated test site",
        },
    )
    assert site_response.status_code == 201
    site = site_response.json()

    area_response = await client.post(
        "/areas",
        headers=admin_headers,
        json={
            "site_id": site["id"],
            "name": "Production Area",
            "code": "TEST-AREA",
            "description": "Automated test production area",
        },
    )
    assert area_response.status_code == 201
    area = area_response.json()

    line_response = await client.post(
        "/production-lines",
        headers=admin_headers,
        json={
            "area_id": area["id"],
            "name": "Production Line 1",
            "code": "TEST-LINE",
            "description": "Automated test production line",
        },
    )
    assert line_response.status_code == 201
    production_line = line_response.json()

    return {
        "organization_id": organization["id"],
        "site_id": site["id"],
        "area_id": area["id"],
        "production_line_id": production_line["id"],
    }


async def test_complete_hierarchy_navigation(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_base_hierarchy(
        client,
        auth_headers["admin"],
    )

    machine_response = await client.post(
        "/machines",
        headers=auth_headers["admin"],
        json={
            "area_id": hierarchy["area_id"],
            "production_line_id": hierarchy["production_line_id"],
            "name": "Test Motor",
            "code": "TEST-MOTOR",
            "location": "Production Line 1",
            "status": "active",
        },
    )

    assert machine_response.status_code == 201
    machine = machine_response.json()

    sites_response = await client.get(
        f"/organizations/{hierarchy['organization_id']}/sites",
        headers=auth_headers["operator"],
    )

    assert sites_response.status_code == 200
    assert len(sites_response.json()) == 1
    assert sites_response.json()[0]["id"] == hierarchy["site_id"]

    areas_response = await client.get(
        f"/sites/{hierarchy['site_id']}/areas",
        headers=auth_headers["operator"],
    )

    assert areas_response.status_code == 200
    assert len(areas_response.json()) == 1
    assert areas_response.json()[0]["id"] == hierarchy["area_id"]

    lines_response = await client.get(
        f"/areas/{hierarchy['area_id']}/production-lines",
        headers=auth_headers["operator"],
    )

    assert lines_response.status_code == 200
    assert len(lines_response.json()) == 1
    assert (
        lines_response.json()[0]["id"]
        == hierarchy["production_line_id"]
    )

    area_machines_response = await client.get(
        f"/areas/{hierarchy['area_id']}/machines",
        headers=auth_headers["operator"],
    )

    assert area_machines_response.status_code == 200
    assert len(area_machines_response.json()) == 1
    assert area_machines_response.json()[0]["id"] == machine["id"]

    line_machines_response = await client.get(
        f"/production-lines/{hierarchy['production_line_id']}/machines",
        headers=auth_headers["operator"],
    )

    assert line_machines_response.status_code == 200
    assert len(line_machines_response.json()) == 1
    assert line_machines_response.json()[0]["id"] == machine["id"]


async def test_operator_cannot_modify_hierarchy(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    response = await client.post(
        "/organizations",
        headers=auth_headers["operator"],
        json={
            "name": "Forbidden Organization",
            "code": "FORBIDDEN-ORG",
            "description": "RBAC test",
        },
    )

    assert response.status_code == 403


async def test_duplicate_organization_code_is_rejected(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    payload = {
        "name": "Organization One",
        "code": "DUPLICATE-ORG",
        "description": "Duplicate test",
    }

    first_response = await client.post(
        "/organizations",
        headers=auth_headers["admin"],
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = await client.post(
        "/organizations",
        headers=auth_headers["admin"],
        json={
            **payload,
            "name": "Organization Two",
        },
    )

    assert second_response.status_code == 409
    assert (
        second_response.json()["detail"]
        == "Organization code already exists"
    )


async def test_invalid_hierarchy_parents_are_rejected(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    site_response = await client.post(
        "/sites",
        headers=auth_headers["admin"],
        json={
            "organization_id": 999999,
            "name": "Invalid Site",
            "code": "INVALID-SITE",
            "location": "Test",
            "description": "Invalid parent test",
        },
    )

    assert site_response.status_code == 404
    assert site_response.json()["detail"] == "Organization not found"

    area_response = await client.post(
        "/areas",
        headers=auth_headers["admin"],
        json={
            "site_id": 999999,
            "name": "Invalid Area",
            "code": "INVALID-AREA",
            "description": "Invalid parent test",
        },
    )

    assert area_response.status_code == 404
    assert area_response.json()["detail"] == "Site not found"

    line_response = await client.post(
        "/production-lines",
        headers=auth_headers["admin"],
        json={
            "area_id": 999999,
            "name": "Invalid Line",
            "code": "INVALID-LINE",
            "description": "Invalid parent test",
        },
    )

    assert line_response.status_code == 404
    assert line_response.json()["detail"] == "Area not found"


async def test_machine_hierarchy_consistency(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_base_hierarchy(
        client,
        auth_headers["admin"],
    )

    utilities_response = await client.post(
        "/areas",
        headers=auth_headers["admin"],
        json={
            "site_id": hierarchy["site_id"],
            "name": "Utilities Area",
            "code": "TEST-UTILITIES",
            "description": "Standalone utility assets",
        },
    )

    assert utilities_response.status_code == 201
    utilities_area = utilities_response.json()

    invalid_machine_response = await client.post(
        "/machines",
        headers=auth_headers["admin"],
        json={
            "area_id": utilities_area["id"],
            "production_line_id": hierarchy["production_line_id"],
            "name": "Invalid Motor",
            "code": "INVALID-MOTOR",
            "location": "Utilities",
            "status": "active",
        },
    )

    assert invalid_machine_response.status_code == 400
    assert (
        invalid_machine_response.json()["detail"]
        == "Production line does not belong to the selected area"
    )

    standalone_machine_response = await client.post(
        "/machines",
        headers=auth_headers["admin"],
        json={
            "area_id": utilities_area["id"],
            "production_line_id": None,
            "name": "Air Compressor 01",
            "code": "TEST-COMPRESSOR",
            "location": "Utilities Area",
            "status": "active",
        },
    )

    assert standalone_machine_response.status_code == 201

    standalone_machine = standalone_machine_response.json()

    assert standalone_machine["area_id"] == utilities_area["id"]
    assert standalone_machine["production_line_id"] is None


async def test_machine_partial_patch_cannot_break_hierarchy(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_base_hierarchy(
        client,
        auth_headers["admin"],
    )

    utilities_response = await client.post(
        "/areas",
        headers=auth_headers["admin"],
        json={
            "site_id": hierarchy["site_id"],
            "name": "Utilities Area",
            "code": "PATCH-UTILITIES",
            "description": "PATCH hierarchy test area",
        },
    )

    assert utilities_response.status_code == 201
    utilities_area = utilities_response.json()

    machine_response = await client.post(
        "/machines",
        headers=auth_headers["admin"],
        json={
            "area_id": hierarchy["area_id"],
            "production_line_id": hierarchy["production_line_id"],
            "name": "Patch Test Motor",
            "code": "PATCH-MOTOR",
            "location": "Production Line 1",
            "status": "active",
        },
    )

    assert machine_response.status_code == 201
    machine = machine_response.json()

    patch_response = await client.patch(
        f"/machines/{machine['id']}",
        headers=auth_headers["admin"],
        json={
            "area_id": utilities_area["id"],
        },
    )

    assert patch_response.status_code == 400
    assert (
        patch_response.json()["detail"]
        == "Production line does not belong to the selected area"
    )

    machine_after_response = await client.get(
        f"/machines/{machine['id']}",
        headers=auth_headers["operator"],
    )

    assert machine_after_response.status_code == 200

    machine_after = machine_after_response.json()

    assert machine_after["area_id"] == hierarchy["area_id"]
    assert (
        machine_after["production_line_id"]
        == hierarchy["production_line_id"]
    )



async def test_machine_sensor_navigation(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_base_hierarchy(
        client,
        auth_headers["admin"],
    )

    machine_response = await client.post(
        "/machines",
        headers=auth_headers["admin"],
        json={
            "area_id": hierarchy["area_id"],
            "production_line_id": hierarchy["production_line_id"],
            "name": "Sensor Test Motor",
            "code": "SENSOR-MOTOR",
            "location": "Production Line 1",
            "status": "active",
        },
    )

    assert machine_response.status_code == 201
    machine = machine_response.json()

    second_machine_response = await client.post(
        "/machines",
        headers=auth_headers["admin"],
        json={
            "area_id": hierarchy["area_id"],
            "production_line_id": hierarchy["production_line_id"],
            "name": "Second Sensor Motor",
            "code": "SENSOR-MOTOR-2",
            "location": "Production Line 1",
            "status": "active",
        },
    )

    assert second_machine_response.status_code == 201
    second_machine = second_machine_response.json()

    first_sensor_response = await client.post(
        "/sensors",
        headers=auth_headers["admin"],
        json={
            "machine_id": machine["id"],
            "name": "Motor Temperature",
            "sensor_type": "temperature",
            "unit": "°C",
            "status": "active",
        },
    )

    assert first_sensor_response.status_code == 201

    second_sensor_response = await client.post(
        "/sensors",
        headers=auth_headers["admin"],
        json={
            "machine_id": machine["id"],
            "name": "Motor Vibration",
            "sensor_type": "vibration",
            "unit": "mm/s",
            "status": "active",
        },
    )

    assert second_sensor_response.status_code == 201

    unrelated_sensor_response = await client.post(
        "/sensors",
        headers=auth_headers["admin"],
        json={
            "machine_id": second_machine["id"],
            "name": "Other Motor Temperature",
            "sensor_type": "temperature",
            "unit": "°C",
            "status": "active",
        },
    )

    assert unrelated_sensor_response.status_code == 201

    response = await client.get(
        f"/machines/{machine['id']}/sensors",
        headers=auth_headers["operator"],
    )

    assert response.status_code == 200

    sensors = response.json()

    assert len(sensors) == 2

    assert [
        sensor["id"]
        for sensor in sensors
    ] == sorted(
        sensor["id"]
        for sensor in sensors
    )

    assert all(
        sensor["machine_id"] == machine["id"]
        for sensor in sensors
    )

    assert {
        sensor["name"]
        for sensor in sensors
    } == {
        "Motor Temperature",
        "Motor Vibration",
    }


async def test_machine_sensor_navigation_returns_empty_for_machine_without_sensors(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_base_hierarchy(
        client,
        auth_headers["admin"],
    )

    machine_response = await client.post(
        "/machines",
        headers=auth_headers["admin"],
        json={
            "area_id": hierarchy["area_id"],
            "production_line_id": hierarchy["production_line_id"],
            "name": "No Sensor Motor",
            "code": "NO-SENSOR-MOTOR",
            "location": "Production Line 1",
            "status": "active",
        },
    )

    assert machine_response.status_code == 201
    machine = machine_response.json()

    response = await client.get(
        f"/machines/{machine['id']}/sensors",
        headers=auth_headers["operator"],
    )

    assert response.status_code == 200
    assert response.json() == []


async def test_machine_sensor_navigation_rejects_unknown_machine(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    response = await client.get(
        "/machines/999999/sensors",
        headers=auth_headers["operator"],
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Machine not found"



async def test_machine_telemetry_returns_latest_and_recent_readings(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_base_hierarchy(
        client,
        auth_headers["admin"],
    )

    machine_response = await client.post(
        "/machines",
        headers=auth_headers["admin"],
        json={
            "area_id": hierarchy["area_id"],
            "production_line_id": hierarchy["production_line_id"],
            "name": "Telemetry Motor",
            "code": "TELEMETRY-MOTOR",
            "location": "Production Line 1",
            "status": "active",
        },
    )

    assert machine_response.status_code == 201
    machine = machine_response.json()

    sensor_response = await client.post(
        "/sensors",
        headers=auth_headers["admin"],
        json={
            "machine_id": machine["id"],
            "name": "Motor Temperature",
            "sensor_type": "temperature",
            "unit": "°C",
            "status": "active",
        },
    )

    assert sensor_response.status_code == 201
    sensor = sensor_response.json()

    for value in [50.0, 52.5, 55.0]:
        reading_response = await client.post(
            "/sensor-readings",
            headers=auth_headers["technician"],
            json={
                "sensor_id": sensor["id"],
                "value": value,
            },
        )

        assert reading_response.status_code == 201

    telemetry_response = await client.get(
        f"/machines/{machine['id']}/telemetry",
        headers=auth_headers["operator"],
        params={
            "limit_per_sensor": 2,
        },
    )

    assert telemetry_response.status_code == 200

    telemetry = telemetry_response.json()

    assert telemetry["machine_id"] == machine["id"]
    assert len(telemetry["sensors"]) == 1

    telemetry_sensor = telemetry["sensors"][0]

    assert telemetry_sensor["sensor_id"] == sensor["id"]
    assert telemetry_sensor["latest_reading"]["value"] == 55.0
    assert len(
        telemetry_sensor["recent_readings"]
    ) == 2


async def test_machine_telemetry_includes_sensors_without_readings(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_base_hierarchy(
        client,
        auth_headers["admin"],
    )

    machine_response = await client.post(
        "/machines",
        headers=auth_headers["admin"],
        json={
            "area_id": hierarchy["area_id"],
            "production_line_id": hierarchy["production_line_id"],
            "name": "Idle Telemetry Motor",
            "code": "IDLE-TELEMETRY-MOTOR",
            "location": "Production Line 1",
            "status": "active",
        },
    )

    assert machine_response.status_code == 201
    machine = machine_response.json()

    sensor_response = await client.post(
        "/sensors",
        headers=auth_headers["admin"],
        json={
            "machine_id": machine["id"],
            "name": "Motor Vibration",
            "sensor_type": "vibration",
            "unit": "mm/s",
            "status": "active",
        },
    )

    assert sensor_response.status_code == 201

    response = await client.get(
        f"/machines/{machine['id']}/telemetry",
        headers=auth_headers["operator"],
    )

    assert response.status_code == 200

    telemetry_sensor = response.json()[
        "sensors"
    ][0]

    assert telemetry_sensor["latest_reading"] is None
    assert telemetry_sensor["recent_readings"] == []


async def test_machine_telemetry_rejects_unknown_machine(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    response = await client.get(
        "/machines/999999/telemetry",
        headers=auth_headers["operator"],
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Machine not found"