import jwt
import pytest
from httpx import AsyncClient

from app.db.session import AsyncSessionLocal
from app.schemas.sensor_reading import SensorReadingCreate
from app.services.ai_automation_service import process_sensor_reading
from app.services.ai_processing_state_service import (
    get_ai_processing_state,
)
from app.services.sensor_reading_service import (
    create_sensor_reading,
    get_sensor_reading_by_id,
)


class FailingInferenceEngine:
    model_name = "failing-test-engine"
    model_version = "1.0"

    def infer(
        self,
        current_value: float,
        history,
    ):
        raise RuntimeError(
            "forced inference failure"
        )


async def create_processing_state_test_sensor(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> int:
    organization_response = await client.post(
        "/organizations",
        headers=admin_headers,
        json={
            "name": "AI Processing State Industries",
            "code": "AI-STATE-ORG",
            "description": "AI processing observability tests",
        },
    )

    assert organization_response.status_code == 201
    organization = organization_response.json()

    site_response = await client.post(
        "/sites",
        headers=admin_headers,
        json={
            "organization_id": organization["id"],
            "name": "AI Processing State Site",
            "code": "AI-STATE-SITE",
            "location": "Test",
            "description": "AI processing observability test site",
        },
    )

    assert site_response.status_code == 201
    site = site_response.json()

    area_response = await client.post(
        "/areas",
        headers=admin_headers,
        json={
            "site_id": site["id"],
            "name": "AI Processing State Area",
            "code": "AI-STATE-AREA",
            "description": "AI processing observability test area",
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
            "name": "AI Processing State Machine",
            "code": "AI-STATE-MACHINE",
            "location": "AI Processing State Area",
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
            "name": "AI Processing State Sensor",
            "sensor_type": "temperature",
            "unit": "celsius",
            "status": "active",
        },
    )

    assert sensor_response.status_code == 201

    return sensor_response.json()["id"]


async def test_successful_processing_is_recorded(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    sensor_id = await create_processing_state_test_sensor(
        client,
        auth_headers["admin"],
    )

    response = await client.post(
        "/sensor-readings",
        headers=auth_headers["admin"],
        json={
            "sensor_id": sensor_id,
            "value": 50.0,
        },
    )

    assert response.status_code == 201

    reading_id = response.json()["id"]

    async with AsyncSessionLocal() as db:
        state = await get_ai_processing_state(
            db,
            source_reading_id=reading_id,
            model_name="statistical-zscore",
            model_version="1.0",
        )

        assert state is not None

        assert state.status == "succeeded"
        assert state.attempt_count == 1

        assert state.first_started_at is not None
        assert state.last_attempt_at is not None
        assert state.completed_at is not None

        assert state.last_error is None


async def test_reprocessing_increments_attempt_count(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    sensor_id = await create_processing_state_test_sensor(
        client,
        auth_headers["admin"],
    )

    response = await client.post(
        "/sensor-readings",
        headers=auth_headers["admin"],
        json={
            "sensor_id": sensor_id,
            "value": 50.0,
        },
    )

    assert response.status_code == 201

    reading_id = response.json()["id"]

    async with AsyncSessionLocal() as db:
        reading = await get_sensor_reading_by_id(
            db,
            reading_id,
        )

        assert reading is not None

        first_state = await get_ai_processing_state(
            db,
            source_reading_id=reading_id,
            model_name="statistical-zscore",
            model_version="1.0",
        )

        assert first_state is not None

        state_id = first_state.id

        assert first_state.attempt_count == 1
        assert first_state.status == "succeeded"

        await process_sensor_reading(
            db,
            reading,
        )

        await process_sensor_reading(
            db,
            reading,
        )

        final_state = await get_ai_processing_state(
            db,
            source_reading_id=reading_id,
            model_name="statistical-zscore",
            model_version="1.0",
        )

        assert final_state is not None

        # Retry attempts update the same state row.
        assert final_state.id == state_id

        # Original API processing + two retries.
        assert final_state.attempt_count == 3

        assert final_state.status == "succeeded"
        assert final_state.completed_at is not None
        assert final_state.last_error is None


async def test_disabled_ai_is_recorded_as_skipped(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    sensor_id = await create_processing_state_test_sensor(
        client,
        auth_headers["admin"],
    )

    config_response = await client.post(
        f"/sensors/{sensor_id}/ai-config",
        headers=auth_headers["admin"],
        json={
            "is_enabled": False,
            "engine_name": "statistical-zscore",
            "anomaly_threshold": 3.0,
            "min_history": 5,
            "history_limit": 10,
            "high_risk_threshold": 5.0,
            "critical_risk_threshold": 8.0,
        },
    )

    assert config_response.status_code == 201

    reading_response = await client.post(
        "/sensor-readings",
        headers=auth_headers["admin"],
        json={
            "sensor_id": sensor_id,
            "value": 999.0,
        },
    )

    assert reading_response.status_code == 201

    reading_id = reading_response.json()["id"]

    async with AsyncSessionLocal() as db:
        state = await get_ai_processing_state(
            db,
            source_reading_id=reading_id,
            model_name="statistical-zscore",
            model_version="1.0",
        )

        assert state is not None

        assert state.status == "skipped"
        assert state.attempt_count == 1
        assert state.completed_at is not None
        assert state.last_error is None


async def test_failed_processing_records_error(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    sensor_id = await create_processing_state_test_sensor(
        client,
        auth_headers["admin"],
    )

    # Create the SensorReading directly through the service.
    #
    # We deliberately do not use POST /sensor-readings here
    # because that endpoint would automatically process it
    # successfully before we can inject our failing engine.
    async with AsyncSessionLocal() as db:
        reading = await create_sensor_reading(
            db,
            SensorReadingCreate(
                sensor_id=sensor_id,
                value=75.0,
            ),
        )

        reading_id = reading.id

        with pytest.raises(
            RuntimeError,
            match="forced inference failure",
        ):
            await process_sensor_reading(
                db,
                reading,
                engine=FailingInferenceEngine(),
            )

        state = await get_ai_processing_state(
            db,
            source_reading_id=reading_id,
            model_name="failing-test-engine",
            model_version="1.0",
        )

        assert state is not None

        assert state.status == "failed"
        assert state.attempt_count == 1

        assert state.completed_at is not None

        assert (
            state.last_error
            == "forced inference failure"
        )

@pytest.mark.parametrize(
    "role_name",
    [
        "admin",
        "manager",
        "technician",
        "operator",
    ],
)
async def test_all_roles_can_read_ai_processing_states(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
    role_name: str,
) -> None:
    sensor_id = await create_processing_state_test_sensor(
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

    response = await client.get(
        f"/sensor-readings/{reading_id}/ai-processing-states",
        headers=auth_headers[role_name],
    )

    assert response.status_code == 200

    states = response.json()

    assert len(states) == 1

    state = states[0]

    assert state["source_reading_id"] == reading_id
    assert state["model_name"] == "statistical-zscore"
    assert state["model_version"] == "1.0"

    assert state["status"] == "succeeded"
    assert state["attempt_count"] == 1

    assert state["first_started_at"] is not None
    assert state["last_attempt_at"] is not None
    assert state["completed_at"] is not None

    assert state["last_error"] is None


async def test_ai_processing_states_returns_404_for_missing_reading(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    response = await client.get(
        "/sensor-readings/999999/ai-processing-states",
        headers=auth_headers["admin"],
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Sensor reading not found"
    }

async def test_duplicate_manual_prediction_returns_409(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    sensor_id = await create_processing_state_test_sensor(
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

    predictions_response = await client.get(
        f"/sensors/{sensor_id}/predictions",
        headers=auth_headers["admin"],
    )

    assert predictions_response.status_code == 200

    predictions = predictions_response.json()

    prediction = next(
        item
        for item in predictions
        if item["source_reading_id"] == reading_id
        and item["model_name"] == "statistical-zscore"
        and item["model_version"] == "1.0"
    )

    duplicate_response = await client.post(
        "/predictions",
        headers=auth_headers["admin"],
        json={
            "sensor_id": prediction["sensor_id"],
            "source_reading_id": prediction["source_reading_id"],
            "predicted_value": prediction["predicted_value"],
            "anomaly_score": prediction["anomaly_score"],
            "is_anomaly": prediction["is_anomaly"],
            "model_name": prediction["model_name"],
            "model_version": prediction["model_version"],
        },
    )

    assert duplicate_response.status_code == 409

    assert duplicate_response.json() == {
        "detail": (
            "Prediction already exists for this source reading "
            "and model version"
        )
    }


async def test_duplicate_manual_alert_for_prediction_returns_409(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    sensor_id = await create_processing_state_test_sensor(
        client,
        auth_headers["admin"],
    )

    prediction_response = await client.post(
        "/predictions",
        headers=auth_headers["admin"],
        json={
            "sensor_id": sensor_id,
            "source_reading_id": None,
            "predicted_value": 75.0,
            "anomaly_score": 6.0,
            "is_anomaly": True,
            "model_name": "manual-alert-test",
            "model_version": "1.0",
        },
    )

    assert prediction_response.status_code == 201

    prediction_id = prediction_response.json()["id"]

    alert_payload = {
        "sensor_id": sensor_id,
        "prediction_id": prediction_id,
        "severity": "high",
        "title": "Manual Prediction Alert",
        "message": "Manual alert conflict test",
        "status": "open",
    }

    first_response = await client.post(
        "/alerts",
        headers=auth_headers["admin"],
        json=alert_payload,
    )

    assert first_response.status_code == 201

    duplicate_response = await client.post(
        "/alerts",
        headers=auth_headers["admin"],
        json=alert_payload,
    )

    assert duplicate_response.status_code == 409

    assert duplicate_response.json() == {
        "detail": "Alert already exists for this prediction"
    }


async def test_duplicate_manual_notification_returns_409(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    sensor_id = await create_processing_state_test_sensor(
        client,
        auth_headers["admin"],
    )

    alert_response = await client.post(
        "/alerts",
        headers=auth_headers["admin"],
        json={
            "sensor_id": sensor_id,
            "prediction_id": None,
            "severity": "medium",
            "title": "Notification Conflict Alert",
            "message": "Alert used for notification conflict testing",
            "status": "open",
        },
    )

    assert alert_response.status_code == 201

    alert_id = alert_response.json()["id"]

    authorization = auth_headers["admin"]["Authorization"]

    token = authorization.split(" ", 1)[1]

    payload = jwt.decode(
        token,
        options={
            "verify_signature": False,
        },
    )

    admin_user_id = int(payload["sub"])

    notification_payload = {
        "user_id": admin_user_id,
        "alert_id": alert_id,
        "title": "Manual Notification",
        "message": "Manual notification conflict test",
        "channel": "in_app",
        "is_read": False,
    }

    first_response = await client.post(
        "/notifications",
        headers=auth_headers["admin"],
        json=notification_payload,
    )

    assert first_response.status_code == 201

    duplicate_response = await client.post(
        "/notifications",
        headers=auth_headers["admin"],
        json=notification_payload,
    )

    assert duplicate_response.status_code == 409

    assert duplicate_response.json() == {
        "detail": (
            "Notification already exists for this user, "
            "alert, and channel"
        )
    }