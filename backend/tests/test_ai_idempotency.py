from httpx import AsyncClient
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.alert import Alert
from app.models.notification import Notification
from app.models.prediction import Prediction
from app.services.ai_automation_service import process_sensor_reading
from app.services.sensor_reading_service import get_sensor_reading_by_id


async def create_idempotency_test_sensor(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> int:
    organization_response = await client.post(
        "/organizations",
        headers=admin_headers,
        json={
            "name": "AI Idempotency Industries",
            "code": "AI-IDEMP-ORG",
            "description": "AI retry safety tests",
        },
    )

    assert organization_response.status_code == 201
    organization = organization_response.json()

    site_response = await client.post(
        "/sites",
        headers=admin_headers,
        json={
            "organization_id": organization["id"],
            "name": "AI Idempotency Site",
            "code": "AI-IDEMP-SITE",
            "location": "Test",
            "description": "AI retry safety test site",
        },
    )

    assert site_response.status_code == 201
    site = site_response.json()

    area_response = await client.post(
        "/areas",
        headers=admin_headers,
        json={
            "site_id": site["id"],
            "name": "AI Idempotency Area",
            "code": "AI-IDEMP-AREA",
            "description": "AI retry safety test area",
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
            "name": "AI Idempotency Machine",
            "code": "AI-IDEMP-MACHINE",
            "location": "AI Idempotency Area",
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
            "name": "AI Idempotency Sensor",
            "sensor_type": "temperature",
            "unit": "celsius",
            "status": "active",
        },
    )

    assert sensor_response.status_code == 201

    return sensor_response.json()["id"]


async def test_same_anomalous_reading_can_be_reprocessed_safely(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    sensor_id = await create_idempotency_test_sensor(
        client,
        auth_headers["admin"],
    )

    # Build the default 10-reading baseline.
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

    # This request already triggers the complete AI pipeline once:
    #
    # SensorReading
    # -> Prediction
    # -> Alert
    # -> Notifications
    anomaly_response = await client.post(
        "/sensor-readings",
        headers=auth_headers["admin"],
        json={
            "sensor_id": sensor_id,
            "value": 80.0,
        },
    )

    assert anomaly_response.status_code == 201

    anomalous_reading_id = anomaly_response.json()["id"]

    async with AsyncSessionLocal() as db:
        reading = await get_sensor_reading_by_id(
            db,
            anomalous_reading_id,
        )

        assert reading is not None

        # Deliberately process the exact same persisted
        # SensorReading again.
        first_retry_result = await process_sensor_reading(
            db,
            reading,
        )

        # And retry it once more to prove repeated calls
        # remain safe.
        second_retry_result = await process_sensor_reading(
            db,
            reading,
        )

        assert first_retry_result is not None
        assert second_retry_result is not None

        # There must still be exactly one Prediction for this
        # reading/model/version.
        prediction_result = await db.execute(
            select(Prediction).where(
                Prediction.source_reading_id
                == anomalous_reading_id,
                Prediction.model_name
                == "statistical-zscore",
                Prediction.model_version
                == "1.0",
            )
        )

        predictions = list(
            prediction_result.scalars().all()
        )

        assert len(predictions) == 1

        prediction = predictions[0]

        assert prediction.is_anomaly is True

        # All retry calls must resolve to the same Prediction.
        assert first_retry_result.id == prediction.id
        assert second_retry_result.id == prediction.id

        # There must still be exactly one Alert for that
        # Prediction.
        alert_result = await db.execute(
            select(Alert).where(
                Alert.prediction_id == prediction.id
            )
        )

        alerts = list(
            alert_result.scalars().all()
        )

        assert len(alerts) == 1

        alert = alerts[0]

        # Admin + Manager + Technician should each have exactly
        # one in-app Notification for the Alert.
        notification_result = await db.execute(
            select(Notification).where(
                Notification.alert_id == alert.id,
                Notification.channel == "in_app",
            )
        )

        notifications = list(
            notification_result.scalars().all()
        )

        assert len(notifications) == 3

        notified_user_ids = {
            notification.user_id
            for notification in notifications
        }

        assert len(notified_user_ids) == 3