import pytest
from httpx import AsyncClient


async def create_runtime_test_machine(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> int:
    organization_response = await client.post(
        "/organizations",
        headers=admin_headers,
        json={
            "name": "AI Runtime Test Industries",
            "code": "AI-RUNTIME-ORG",
            "description": "Sensor AI runtime configuration tests",
        },
    )

    assert organization_response.status_code == 201
    organization = organization_response.json()

    site_response = await client.post(
        "/sites",
        headers=admin_headers,
        json={
            "organization_id": organization["id"],
            "name": "AI Runtime Test Site",
            "code": "AI-RUNTIME-SITE",
            "location": "Test",
            "description": "AI runtime configuration test site",
        },
    )

    assert site_response.status_code == 201
    site = site_response.json()

    area_response = await client.post(
        "/areas",
        headers=admin_headers,
        json={
            "site_id": site["id"],
            "name": "AI Runtime Test Area",
            "code": "AI-RUNTIME-AREA",
            "description": "AI runtime configuration test area",
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
            "name": "AI Runtime Test Machine",
            "code": "AI-RUNTIME-MACHINE",
            "location": "AI Runtime Test Area",
            "status": "active",
        },
    )

    assert machine_response.status_code == 201

    return machine_response.json()["id"]


async def create_runtime_test_sensor(
    client: AsyncClient,
    admin_headers: dict[str, str],
    machine_id: int,
    name: str,
) -> int:
    response = await client.post(
        "/sensors",
        headers=admin_headers,
        json={
            "machine_id": machine_id,
            "name": name,
            "sensor_type": "temperature",
            "unit": "celsius",
            "status": "active",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


async def create_ai_config(
    client: AsyncClient,
    admin_headers: dict[str, str],
    sensor_id: int,
    *,
    is_enabled: bool = True,
    anomaly_threshold: float = 3.0,
    min_history: int = 5,
    history_limit: int = 10,
    high_risk_threshold: float = 5.0,
    critical_risk_threshold: float = 8.0,
) -> None:
    response = await client.post(
        f"/sensors/{sensor_id}/ai-config",
        headers=admin_headers,
        json={
            "is_enabled": is_enabled,
            "engine_name": "statistical-zscore",
            "anomaly_threshold": anomaly_threshold,
            "min_history": min_history,
            "history_limit": history_limit,
            "high_risk_threshold": high_risk_threshold,
            "critical_risk_threshold": critical_risk_threshold,
        },
    )

    assert response.status_code == 201


async def post_reading(
    client: AsyncClient,
    admin_headers: dict[str, str],
    sensor_id: int,
    value: float,
) -> dict:
    response = await client.post(
        "/sensor-readings",
        headers=admin_headers,
        json={
            "sensor_id": sensor_id,
            "value": value,
        },
    )

    assert response.status_code == 201

    return response.json()


async def post_baseline(
    client: AsyncClient,
    admin_headers: dict[str, str],
    sensor_id: int,
) -> None:
    for value in [
        48.0,
        49.0,
        50.0,
        51.0,
        52.0,
    ]:
        await post_reading(
            client,
            admin_headers,
            sensor_id,
            value,
        )


async def get_prediction_for_reading(
    client: AsyncClient,
    headers: dict[str, str],
    sensor_id: int,
    reading_id: int,
) -> dict:
    response = await client.get(
        f"/sensors/{sensor_id}/predictions",
        headers=headers,
    )

    assert response.status_code == 200

    predictions = response.json()

    return next(
        prediction
        for prediction in predictions
        if prediction["source_reading_id"] == reading_id
    )


async def get_alert_for_prediction(
    client: AsyncClient,
    headers: dict[str, str],
    sensor_id: int,
    prediction_id: int,
) -> dict | None:
    response = await client.get(
        f"/sensors/{sensor_id}/alerts",
        headers=headers,
    )

    assert response.status_code == 200

    alerts = response.json()

    return next(
        (
            alert
            for alert in alerts
            if alert["prediction_id"] == prediction_id
        ),
        None,
    )


async def test_sensor_specific_anomaly_threshold_changes_behavior(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    machine_id = await create_runtime_test_machine(
        client,
        auth_headers["admin"],
    )

    strict_sensor_id = await create_runtime_test_sensor(
        client,
        auth_headers["admin"],
        machine_id,
        "Strict Threshold Sensor",
    )

    sensitive_sensor_id = await create_runtime_test_sensor(
        client,
        auth_headers["admin"],
        machine_id,
        "Sensitive Threshold Sensor",
    )

    await create_ai_config(
        client,
        auth_headers["admin"],
        strict_sensor_id,
        anomaly_threshold=3.0,
    )

    await create_ai_config(
        client,
        auth_headers["admin"],
        sensitive_sensor_id,
        anomaly_threshold=2.0,
    )

    await post_baseline(
        client,
        auth_headers["admin"],
        strict_sensor_id,
    )

    await post_baseline(
        client,
        auth_headers["admin"],
        sensitive_sensor_id,
    )

    strict_reading = await post_reading(
        client,
        auth_headers["admin"],
        strict_sensor_id,
        54.0,
    )

    sensitive_reading = await post_reading(
        client,
        auth_headers["admin"],
        sensitive_sensor_id,
        54.0,
    )

    strict_prediction = await get_prediction_for_reading(
        client,
        auth_headers["admin"],
        strict_sensor_id,
        strict_reading["id"],
    )

    sensitive_prediction = await get_prediction_for_reading(
        client,
        auth_headers["admin"],
        sensitive_sensor_id,
        sensitive_reading["id"],
    )

    assert strict_prediction["anomaly_score"] == pytest.approx(
        sensitive_prediction["anomaly_score"]
    )

    assert 2.0 < strict_prediction["anomaly_score"] < 3.0

    assert strict_prediction["is_anomaly"] is False
    assert sensitive_prediction["is_anomaly"] is True

    strict_alert = await get_alert_for_prediction(
        client,
        auth_headers["admin"],
        strict_sensor_id,
        strict_prediction["id"],
    )

    sensitive_alert = await get_alert_for_prediction(
        client,
        auth_headers["admin"],
        sensitive_sensor_id,
        sensitive_prediction["id"],
    )

    assert strict_alert is None
    assert sensitive_alert is not None


async def test_disabled_sensor_ai_skips_automation(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    machine_id = await create_runtime_test_machine(
        client,
        auth_headers["admin"],
    )

    sensor_id = await create_runtime_test_sensor(
        client,
        auth_headers["admin"],
        machine_id,
        "Disabled AI Sensor",
    )

    await create_ai_config(
        client,
        auth_headers["admin"],
        sensor_id,
        is_enabled=False,
    )

    reading = await post_reading(
        client,
        auth_headers["admin"],
        sensor_id,
        80.0,
    )

    readings_response = await client.get(
        f"/sensors/{sensor_id}/readings",
        headers=auth_headers["admin"],
    )

    assert readings_response.status_code == 200

    assert any(
        stored_reading["id"] == reading["id"]
        for stored_reading in readings_response.json()
    )

    predictions_response = await client.get(
        f"/sensors/{sensor_id}/predictions",
        headers=auth_headers["admin"],
    )

    assert predictions_response.status_code == 200
    assert predictions_response.json() == []

    alerts_response = await client.get(
        f"/sensors/{sensor_id}/alerts",
        headers=auth_headers["admin"],
    )

    assert alerts_response.status_code == 200
    assert alerts_response.json() == []


async def test_sensor_specific_risk_threshold_changes_alert_severity(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    machine_id = await create_runtime_test_machine(
        client,
        auth_headers["admin"],
    )

    high_sensor_id = await create_runtime_test_sensor(
        client,
        auth_headers["admin"],
        machine_id,
        "High Severity Sensor",
    )

    medium_sensor_id = await create_runtime_test_sensor(
        client,
        auth_headers["admin"],
        machine_id,
        "Medium Severity Sensor",
    )

    await create_ai_config(
        client,
        auth_headers["admin"],
        high_sensor_id,
        anomaly_threshold=2.0,
        high_risk_threshold=2.5,
        critical_risk_threshold=4.0,
    )

    await create_ai_config(
        client,
        auth_headers["admin"],
        medium_sensor_id,
        anomaly_threshold=2.0,
        high_risk_threshold=3.0,
        critical_risk_threshold=4.0,
    )

    await post_baseline(
        client,
        auth_headers["admin"],
        high_sensor_id,
    )

    await post_baseline(
        client,
        auth_headers["admin"],
        medium_sensor_id,
    )

    high_reading = await post_reading(
        client,
        auth_headers["admin"],
        high_sensor_id,
        54.0,
    )

    medium_reading = await post_reading(
        client,
        auth_headers["admin"],
        medium_sensor_id,
        54.0,
    )

    high_prediction = await get_prediction_for_reading(
        client,
        auth_headers["admin"],
        high_sensor_id,
        high_reading["id"],
    )

    medium_prediction = await get_prediction_for_reading(
        client,
        auth_headers["admin"],
        medium_sensor_id,
        medium_reading["id"],
    )

    assert high_prediction["is_anomaly"] is True
    assert medium_prediction["is_anomaly"] is True

    assert high_prediction["anomaly_score"] == pytest.approx(
        medium_prediction["anomaly_score"]
    )

    high_alert = await get_alert_for_prediction(
        client,
        auth_headers["admin"],
        high_sensor_id,
        high_prediction["id"],
    )

    medium_alert = await get_alert_for_prediction(
        client,
        auth_headers["admin"],
        medium_sensor_id,
        medium_prediction["id"],
    )

    assert high_alert is not None
    assert medium_alert is not None

    assert high_alert["severity"] == "high"
    assert medium_alert["severity"] == "medium"


async def test_configured_history_limit_controls_inference_window(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    machine_id = await create_runtime_test_machine(
        client,
        auth_headers["admin"],
    )

    sensor_id = await create_runtime_test_sensor(
        client,
        auth_headers["admin"],
        machine_id,
        "History Window Sensor",
    )

    await create_ai_config(
        client,
        auth_headers["admin"],
        sensor_id,
        anomaly_threshold=3.0,
        min_history=3,
        history_limit=3,
    )

    # Old values should eventually fall outside the configured
    # three-reading inference window.
    for value in [
        100.0,
        100.0,
        100.0,
        10.0,
        10.0,
        10.0,
    ]:
        await post_reading(
            client,
            auth_headers["admin"],
            sensor_id,
            value,
        )

    reading = await post_reading(
        client,
        auth_headers["admin"],
        sensor_id,
        20.0,
    )

    prediction = await get_prediction_for_reading(
        client,
        auth_headers["admin"],
        sensor_id,
        reading["id"],
    )

    # Only the three most recent historical values are used:
    #
    # 10, 10, 10
    #
    # The older 100 values must not influence this prediction.
    assert prediction["predicted_value"] == pytest.approx(10.0)

    assert prediction["is_anomaly"] is True

    # Zero-variance history + a changed value uses the
    # engine's deterministic anomaly score of threshold + 1.
    assert prediction["anomaly_score"] == pytest.approx(4.0)