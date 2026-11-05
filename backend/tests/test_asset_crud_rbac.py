
from httpx import AsyncClient


async def create_test_area(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> int:
    organization_response = await client.post(
        "/organizations",
        headers=admin_headers,
        json={
            "name": "Asset RBAC Organization",
            "code": "ASSET-RBAC-ORG",
            "description": "Asset authorization tests",
        },
    )
    assert organization_response.status_code == 201

    site_response = await client.post(
        "/sites",
        headers=admin_headers,
        json={
            "organization_id": organization_response.json()["id"],
            "name": "Asset RBAC Site",
            "code": "ASSET-RBAC-SITE",
            "location": "Test Location",
            "description": "Asset authorization tests",
        },
    )
    assert site_response.status_code == 201

    area_response = await client.post(
        "/areas",
        headers=admin_headers,
        json={
            "site_id": site_response.json()["id"],
            "name": "Asset RBAC Area",
            "code": "ASSET-RBAC-AREA",
            "description": "Asset authorization tests",
        },
    )
    assert area_response.status_code == 201

    return area_response.json()["id"]


async def create_test_machine(
    client: AsyncClient,
    admin_headers: dict[str, str],
    area_id: int,
    code: str,
) -> dict:
    response = await client.post(
        "/machines",
        headers=admin_headers,
        json={
            "area_id": area_id,
            "production_line_id": None,
            "name": f"Machine {code}",
            "code": code,
            "location": "Asset RBAC Area",
            "status": "active",
        },
    )

    assert response.status_code == 201, response.text
    return response.json()


async def create_test_sensor(
    client: AsyncClient,
    admin_headers: dict[str, str],
    machine_id: int,
    name: str,
) -> dict:
    response = await client.post(
        "/sensors",
        headers=admin_headers,
        json={
            "machine_id": machine_id,
            "name": name,
            "sensor_type": "temperature",
            "unit": "C",
            "status": "active",
        },
    )

    assert response.status_code == 201, response.text
    return response.json()


# =========================================================
# MACHINE RBAC
# =========================================================


async def test_machine_creation_respects_asset_write_roles(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    area_id = await create_test_area(
        client,
        auth_headers["admin"],
    )

    allowed_roles = {"admin", "manager", "technician"}

    for role_name in ("admin", "manager", "technician", "operator"):
        code = f"RBAC-MACHINE-{role_name.upper()}"

        response = await client.post(
            "/machines",
            headers=auth_headers[role_name],
            json={
                "area_id": area_id,
                "production_line_id": None,
                "name": f"Machine {role_name}",
                "code": code,
                "location": "Asset RBAC Area",
                "status": "active",
            },
        )

        expected_status = 201 if role_name in allowed_roles else 403
        assert response.status_code == expected_status, response.text

    machines_response = await client.get(
        "/machines",
        headers=auth_headers["admin"],
    )
    assert machines_response.status_code == 200

    machine_codes = {
        machine["code"]
        for machine in machines_response.json()
    }

    for role_name in ("admin", "manager", "technician"):
        assert f"RBAC-MACHINE-{role_name.upper()}" in machine_codes

    assert "RBAC-MACHINE-OPERATOR" not in machine_codes


async def test_machine_update_respects_asset_write_roles(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    area_id = await create_test_area(
        client,
        auth_headers["admin"],
    )

    machine = await create_test_machine(
        client,
        auth_headers["admin"],
        area_id,
        "RBAC-MACHINE-UPDATE",
    )

    current_name = machine["name"]

    for role_name in ("admin", "manager", "technician", "operator"):
        updated_name = f"Updated by {role_name}"

        response = await client.patch(
            f"/machines/{machine['id']}",
            headers=auth_headers[role_name],
            json={"name": updated_name},
        )

        expected_status = 200 if role_name != "operator" else 403
        assert response.status_code == expected_status, response.text

        machine_after = await client.get(
            f"/machines/{machine['id']}",
            headers=auth_headers["admin"],
        )
        assert machine_after.status_code == 200

        if role_name != "operator":
            current_name = updated_name

        assert machine_after.json()["name"] == current_name


async def test_machine_deletion_respects_management_roles(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    area_id = await create_test_area(
        client,
        auth_headers["admin"],
    )

    allowed_roles = {"admin", "manager"}

    for role_name in ("admin", "manager", "technician", "operator"):
        machine = await create_test_machine(
            client,
            auth_headers["admin"],
            area_id,
            f"RBAC-DELETE-{role_name.upper()}",
        )

        response = await client.delete(
            f"/machines/{machine['id']}",
            headers=auth_headers[role_name],
        )

        expected_status = 204 if role_name in allowed_roles else 403
        assert response.status_code == expected_status, response.text

        machine_after = await client.get(
            f"/machines/{machine['id']}",
            headers=auth_headers["admin"],
        )

        if role_name in allowed_roles:
            assert machine_after.status_code == 404
        else:
            assert machine_after.status_code == 200


# =========================================================
# SENSOR RBAC
# =========================================================


async def test_sensor_creation_respects_asset_write_roles(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    area_id = await create_test_area(
        client,
        auth_headers["admin"],
    )

    machine = await create_test_machine(
        client,
        auth_headers["admin"],
        area_id,
        "RBAC-SENSOR-CREATE-MACHINE",
    )

    allowed_roles = {"admin", "manager", "technician"}

    for role_name in ("admin", "manager", "technician", "operator"):
        sensor_name = f"RBAC Sensor {role_name}"

        response = await client.post(
            "/sensors",
            headers=auth_headers[role_name],
            json={
                "machine_id": machine["id"],
                "name": sensor_name,
                "sensor_type": "temperature",
                "unit": "C",
                "status": "active",
            },
        )

        expected_status = 201 if role_name in allowed_roles else 403
        assert response.status_code == expected_status, response.text

    sensors_response = await client.get(
        "/sensors",
        headers=auth_headers["admin"],
    )
    assert sensors_response.status_code == 200

    sensor_names = {
        sensor["name"]
        for sensor in sensors_response.json()
    }

    for role_name in ("admin", "manager", "technician"):
        assert f"RBAC Sensor {role_name}" in sensor_names

    assert "RBAC Sensor operator" not in sensor_names


async def test_sensor_update_respects_asset_write_roles(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    area_id = await create_test_area(
        client,
        auth_headers["admin"],
    )

    machine = await create_test_machine(
        client,
        auth_headers["admin"],
        area_id,
        "RBAC-SENSOR-UPDATE-MACHINE",
    )

    sensor = await create_test_sensor(
        client,
        auth_headers["admin"],
        machine["id"],
        "Original Sensor Name",
    )

    current_name = sensor["name"]

    for role_name in ("admin", "manager", "technician", "operator"):
        updated_name = f"Updated Sensor by {role_name}"

        response = await client.patch(
            f"/sensors/{sensor['id']}",
            headers=auth_headers[role_name],
            json={"name": updated_name},
        )

        expected_status = 200 if role_name != "operator" else 403
        assert response.status_code == expected_status, response.text

        sensor_after = await client.get(
            f"/sensors/{sensor['id']}",
            headers=auth_headers["admin"],
        )
        assert sensor_after.status_code == 200

        if role_name != "operator":
            current_name = updated_name

        assert sensor_after.json()["name"] == current_name


async def test_sensor_deletion_respects_management_roles(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    area_id = await create_test_area(
        client,
        auth_headers["admin"],
    )

    machine = await create_test_machine(
        client,
        auth_headers["admin"],
        area_id,
        "RBAC-SENSOR-DELETE-MACHINE",
    )

    allowed_roles = {"admin", "manager"}

    for role_name in ("admin", "manager", "technician", "operator"):
        sensor = await create_test_sensor(
            client,
            auth_headers["admin"],
            machine["id"],
            f"Delete Test Sensor {role_name}",
        )

        response = await client.delete(
            f"/sensors/{sensor['id']}",
            headers=auth_headers[role_name],
        )

        expected_status = 204 if role_name in allowed_roles else 403
        assert response.status_code == expected_status, response.text

        sensor_after = await client.get(
            f"/sensors/{sensor['id']}",
            headers=auth_headers["admin"],
        )

        if role_name in allowed_roles:
            assert sensor_after.status_code == 404
        else:
            assert sensor_after.status_code == 200


async def test_machine_and_sensor_reads_are_available_to_all_roles(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    area_id = await create_test_area(
        client,
        auth_headers["admin"],
    )

    machine = await create_test_machine(
        client,
        auth_headers["admin"],
        area_id,
        "RBAC-READ-MACHINE",
    )

    sensor = await create_test_sensor(
        client,
        auth_headers["admin"],
        machine["id"],
        "RBAC Read Sensor",
    )

    for role_name in ("admin", "manager", "technician", "operator"):
        machine_response = await client.get(
            f"/machines/{machine['id']}",
            headers=auth_headers[role_name],
        )
        assert machine_response.status_code == 200

        sensors_response = await client.get(
            "/sensors",
            headers=auth_headers[role_name],
        )
        assert sensors_response.status_code == 200

        sensor_response = await client.get(
            f"/sensors/{sensor['id']}",
            headers=auth_headers[role_name],
        )
        assert sensor_response.status_code == 200
