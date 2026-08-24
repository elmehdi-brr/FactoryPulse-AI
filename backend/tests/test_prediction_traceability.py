from httpx import AsyncClient


async def create_sensor_context(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> dict[str, int]:
    organization_response = await client.post(
        "/organizations",
        headers=admin_headers,
        json={
            "name": "Traceability Industries",
            "code": "TRACE-ORG",
            "description": "Prediction traceability tests",
        },
    )
    assert organization_response.status_code == 201
    organization = organization_response.json()

    site_response = await client.post(
        "/sites",
        headers=admin_headers,
        json={
            "organization_id": organization["id"],
            "name": "Traceability Factory",
            "code": "TRACE-SITE",
            "location": "Test",
            "description": "Prediction traceability test site",
        },
    )
    assert site_response.status_code == 201
    site = site_response.json()

    area_response = await client.post(
        "/areas",
        headers=admin_headers,
        json={
            "site_id": site["id"],
            "name": "Traceability Area",
            "code": "TRACE-AREA",
            "description": "Prediction traceability test area",
        },
    )
    assert area_response.status_code == 201
    area = area_response.json()

    machine_response = await client.post(
        "/machines",
        headers=admin_headers,
        json={
            "area_id": area["id"],
            "production_line_id": None,
            "name": "Traceability Machine",
            "code": "TRACE-MACHINE",
            "location": "Traceability Area",
            "status": "active",
        },
    )
    assert machine_response.status_code == 201
    machine = machine_response.json()

    sensor_response = await client.post(
        "/sensors",
        headers=admin_headers,
        json={
            "machine_id": machine["id"],
            "name": "Temperature Sensor A",
            "sensor_type": "temperature",
            "unit": "celsius",
            "status": "active",
        },
    )
    assert sensor_response.status_code == 201
    sensor = sensor_response.json()

    return {
        "machine_id": machine["id"],
        "sensor_id": sensor["id"],
    }


async def test_prediction_can_reference_source_reading(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    context = await create_sensor_context(
        client,
        auth_headers["admin"],
    )

    reading_response = await client.post(
        "/sensor-readings",
        headers=auth_headers["admin"],
        json={
            "sensor_id": context["sensor_id"],
            "value": 84.5,
        },
    )

    assert reading_response.status_code == 201
    reading = reading_response.json()

    prediction_response = await client.post(
        "/predictions",
        headers=auth_headers["admin"],
        json={
            "sensor_id": context["sensor_id"],
            "source_reading_id": reading["id"],
            "predicted_value": 86.2,
            "anomaly_score": 0.91,
            "is_anomaly": True,
            "model_name": "traceability-test-model",
            "model_version": "1.0",
        },
    )

    assert prediction_response.status_code == 201

    prediction = prediction_response.json()

    assert prediction["sensor_id"] == context["sensor_id"]
    assert prediction["source_reading_id"] == reading["id"]


async def test_prediction_rejects_missing_source_reading(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    context = await create_sensor_context(
        client,
        auth_headers["admin"],
    )

    prediction_response = await client.post(
        "/predictions",
        headers=auth_headers["admin"],
        json={
            "sensor_id": context["sensor_id"],
            "source_reading_id": 999999,
            "predicted_value": 50.0,
            "anomaly_score": 0.2,
            "is_anomaly": False,
            "model_name": "traceability-test-model",
            "model_version": "1.0",
        },
    )

    assert prediction_response.status_code == 404
    assert (
        prediction_response.json()["detail"]
        == "Source sensor reading not found"
    )


async def test_prediction_rejects_reading_from_another_sensor(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    context = await create_sensor_context(
        client,
        auth_headers["admin"],
    )

    second_sensor_response = await client.post(
        "/sensors",
        headers=auth_headers["admin"],
        json={
            "machine_id": context["machine_id"],
            "name": "Temperature Sensor B",
            "sensor_type": "temperature",
            "unit": "celsius",
            "status": "active",
        },
    )

    assert second_sensor_response.status_code == 201
    second_sensor = second_sensor_response.json()

    reading_response = await client.post(
        "/sensor-readings",
        headers=auth_headers["admin"],
        json={
            "sensor_id": second_sensor["id"],
            "value": 70.0,
        },
    )

    assert reading_response.status_code == 201
    reading = reading_response.json()

    prediction_response = await client.post(
        "/predictions",
        headers=auth_headers["admin"],
        json={
            "sensor_id": context["sensor_id"],
            "source_reading_id": reading["id"],
            "predicted_value": 72.0,
            "anomaly_score": 0.4,
            "is_anomaly": False,
            "model_name": "traceability-test-model",
            "model_version": "1.0",
        },
    )

    assert prediction_response.status_code == 400
    assert (
        prediction_response.json()["detail"]
        == "Source reading does not belong to the selected sensor"
    )


async def test_manual_prediction_without_source_reading_still_works(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    context = await create_sensor_context(
        client,
        auth_headers["admin"],
    )

    prediction_response = await client.post(
        "/predictions",
        headers=auth_headers["admin"],
        json={
            "sensor_id": context["sensor_id"],
            "source_reading_id": None,
            "predicted_value": 42.0,
            "anomaly_score": None,
            "is_anomaly": False,
            "model_name": "manual-test",
            "model_version": None,
        },
    )

    assert prediction_response.status_code == 201

    prediction = prediction_response.json()

    assert prediction["source_reading_id"] is None