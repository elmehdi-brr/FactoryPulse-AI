import pytest
from httpx import AsyncClient

from app.db.session import AsyncSessionLocal
from app.services.ai_automation_service import process_sensor_reading
from app.services.sensor_reading_service import get_sensor_reading_by_id


async def create_ai_sensor(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> int:
    organization_response = await client.post(
        "/organizations",
        headers=admin_headers,
        json={
            "name": "AI Test Industries",
            "code": "AI-TEST-ORG",
            "description": "AI automation tests",
        },
    )
    assert organization_response.status_code == 201
    organization = organization_response.json()

    site_response = await client.post(
        "/sites",
        headers=admin_headers,
        json={
            "organization_id": organization["id"],
            "name": "AI Test Factory",
            "code": "AI-TEST-SITE",
            "location": "Test",
            "description": "AI automation test site",
        },
    )
    assert site_response.status_code == 201
    site = site_response.json()

    area_response = await client.post(
        "/areas",
        headers=admin_headers,
        json={
            "site_id": site["id"],
            "name": "AI Test Area",
            "code": "AI-TEST-AREA",
            "description": "AI automation test area",
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
            "name": "AI Test Machine",
            "code": "AI-TEST-MACHINE",
            "location": "AI Test Area",
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
            "name": "AI Temperature Sensor",
            "sensor_type": "temperature",
            "unit": "celsius",
            "status": "active",
        },
    )
    assert sensor_response.status_code == 201

    return sensor_response.json()["id"]


async def test_process_sensor_reading_creates_traceable_prediction(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    sensor_id = await create_ai_sensor(
        client,
        auth_headers["admin"],
    )

    reading_response = await client.post(
        "/sensor-readings",
        headers=auth_headers["admin"],
        json={
            "sensor_id": sensor_id,
            "value": 50.0,
        },
    )

    assert reading_response.status_code == 201
    reading_id = reading_response.json()["id"]

    async with AsyncSessionLocal() as db:
        reading = await get_sensor_reading_by_id(
            db,
            reading_id,
        )

        assert reading is not None

        prediction = await process_sensor_reading(
            db,
            reading,
        )

        assert prediction.sensor_id == sensor_id
        assert prediction.source_reading_id == reading_id
        assert prediction.predicted_value == pytest.approx(50.0)
        assert prediction.anomaly_score is None
        assert prediction.is_anomaly is False
        assert prediction.model_name == "statistical-zscore"
        assert prediction.model_version == "1.0"


async def test_process_sensor_reading_detects_anomaly(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    sensor_id = await create_ai_sensor(
        client,
        auth_headers["admin"],
    )

    for _ in range(10):
        response = await client.post(
            "/sensor-readings",
            headers=auth_headers["admin"],
            json={
                "sensor_id": sensor_id,
                "value": 50.0,
            },
        )

        assert response.status_code == 201

    anomalous_response = await client.post(
        "/sensor-readings",
        headers=auth_headers["admin"],
        json={
            "sensor_id": sensor_id,
            "value": 80.0,
        },
    )

    assert anomalous_response.status_code == 201
    anomalous_reading_id = anomalous_response.json()["id"]

    async with AsyncSessionLocal() as db:
        reading = await get_sensor_reading_by_id(
            db,
            anomalous_reading_id,
        )

        assert reading is not None

        prediction = await process_sensor_reading(
            db,
            reading,
        )

        assert prediction.source_reading_id == anomalous_reading_id
        assert prediction.predicted_value == pytest.approx(50.0)
        assert prediction.anomaly_score is not None
        assert prediction.anomaly_score >= 3.0
        assert prediction.is_anomaly is True

async def test_sensor_reading_api_automatically_creates_prediction(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    sensor_id = await create_ai_sensor(
        client,
        auth_headers["admin"],
    )

    reading_response = await client.post(
        "/sensor-readings",
        headers=auth_headers["admin"],
        json={
            "sensor_id": sensor_id,
            "value": 55.0,
        },
    )

    assert reading_response.status_code == 201

    reading = reading_response.json()

    predictions_response = await client.get(
        f"/sensors/{sensor_id}/predictions",
        headers=auth_headers["operator"],
    )

    assert predictions_response.status_code == 200

    predictions = predictions_response.json()

    assert len(predictions) == 1

    prediction = predictions[0]

    assert prediction["sensor_id"] == sensor_id
    assert prediction["source_reading_id"] == reading["id"]
    assert prediction["predicted_value"] == pytest.approx(55.0)
    assert prediction["anomaly_score"] is None
    assert prediction["is_anomaly"] is False
    assert prediction["model_name"] == "statistical-zscore"
    assert prediction["model_version"] == "1.0"