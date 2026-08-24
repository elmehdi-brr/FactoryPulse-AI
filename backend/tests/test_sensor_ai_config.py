import pytest
from httpx import AsyncClient


async def create_test_sensor(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> int:
    organization_response = await client.post(
        "/organizations",
        headers=admin_headers,
        json={
            "name": "AI Config Test Industries",
            "code": "AI-CONFIG-ORG",
            "description": "AI configuration automated tests",
        },
    )

    assert organization_response.status_code == 201
    organization = organization_response.json()

    site_response = await client.post(
        "/sites",
        headers=admin_headers,
        json={
            "organization_id": organization["id"],
            "name": "AI Config Test Site",
            "code": "AI-CONFIG-SITE",
            "location": "Test",
            "description": "AI configuration test site",
        },
    )

    assert site_response.status_code == 201
    site = site_response.json()

    area_response = await client.post(
        "/areas",
        headers=admin_headers,
        json={
            "site_id": site["id"],
            "name": "AI Config Test Area",
            "code": "AI-CONFIG-AREA",
            "description": "AI configuration test area",
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
            "name": "AI Config Test Machine",
            "code": "AI-CONFIG-MACHINE",
            "location": "AI Config Test Area",
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
            "name": "AI Config Test Sensor",
            "sensor_type": "temperature",
            "unit": "celsius",
            "status": "active",
        },
    )

    assert sensor_response.status_code == 201

    return sensor_response.json()["id"]


async def create_default_ai_config(
    client: AsyncClient,
    admin_headers: dict[str, str],
    sensor_id: int,
):
    response = await client.post(
        f"/sensors/{sensor_id}/ai-config",
        headers=admin_headers,
        json={
            "is_enabled": True,
            "engine_name": "statistical-zscore",
            "anomaly_threshold": 3.0,
            "min_history": 10,
            "history_limit": 50,
            "high_risk_threshold": 5.0,
            "critical_risk_threshold": 8.0,
        },
    )

    assert response.status_code == 201

    return response.json()


async def test_create_sensor_ai_config(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    sensor_id = await create_test_sensor(
        client,
        auth_headers["admin"],
    )

    response = await client.post(
        f"/sensors/{sensor_id}/ai-config",
        headers=auth_headers["admin"],
        json={
            "is_enabled": True,
            "engine_name": "statistical-zscore",
            "anomaly_threshold": 3.5,
            "min_history": 12,
            "history_limit": 60,
            "high_risk_threshold": 6.0,
            "critical_risk_threshold": 9.0,
        },
    )

    assert response.status_code == 201

    config = response.json()

    assert config["sensor_id"] == sensor_id
    assert config["is_enabled"] is True
    assert config["engine_name"] == "statistical-zscore"
    assert config["anomaly_threshold"] == 3.5
    assert config["min_history"] == 12
    assert config["history_limit"] == 60
    assert config["high_risk_threshold"] == 6.0
    assert config["critical_risk_threshold"] == 9.0

    assert "id" in config
    assert "created_at" in config


async def test_get_sensor_ai_config(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    sensor_id = await create_test_sensor(
        client,
        auth_headers["admin"],
    )

    created_config = await create_default_ai_config(
        client,
        auth_headers["admin"],
        sensor_id,
    )

    response = await client.get(
        f"/sensors/{sensor_id}/ai-config",
        headers=auth_headers["operator"],
    )

    assert response.status_code == 200

    config = response.json()

    assert config["id"] == created_config["id"]
    assert config["sensor_id"] == sensor_id
    assert config["engine_name"] == "statistical-zscore"


async def test_patch_sensor_ai_config(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    sensor_id = await create_test_sensor(
        client,
        auth_headers["admin"],
    )

    await create_default_ai_config(
        client,
        auth_headers["admin"],
        sensor_id,
    )

    response = await client.patch(
        f"/sensors/{sensor_id}/ai-config",
        headers=auth_headers["manager"],
        json={
            "anomaly_threshold": 4.0,
            "history_limit": 75,
            "high_risk_threshold": 6.0,
            "critical_risk_threshold": 10.0,
        },
    )

    assert response.status_code == 200

    config = response.json()

    assert config["anomaly_threshold"] == 4.0
    assert config["history_limit"] == 75
    assert config["high_risk_threshold"] == 6.0
    assert config["critical_risk_threshold"] == 10.0

    # Values that were not patched must remain unchanged.
    assert config["min_history"] == 10
    assert config["is_enabled"] is True
    assert config["engine_name"] == "statistical-zscore"


async def test_duplicate_sensor_ai_config_is_rejected(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    sensor_id = await create_test_sensor(
        client,
        auth_headers["admin"],
    )

    await create_default_ai_config(
        client,
        auth_headers["admin"],
        sensor_id,
    )

    response = await client.post(
        f"/sensors/{sensor_id}/ai-config",
        headers=auth_headers["admin"],
        json={
            "is_enabled": True,
            "engine_name": "statistical-zscore",
            "anomaly_threshold": 3.0,
            "min_history": 10,
            "history_limit": 50,
            "high_risk_threshold": 5.0,
            "critical_risk_threshold": 8.0,
        },
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "Sensor AI configuration already exists"
    )


async def test_ai_config_unknown_sensor_returns_404(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    response = await client.post(
        "/sensors/999999/ai-config",
        headers=auth_headers["admin"],
        json={
            "is_enabled": True,
            "engine_name": "statistical-zscore",
            "anomaly_threshold": 3.0,
            "min_history": 10,
            "history_limit": 50,
            "high_risk_threshold": 5.0,
            "critical_risk_threshold": 8.0,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Sensor not found"


async def test_sensor_without_ai_config_returns_404(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    sensor_id = await create_test_sensor(
        client,
        auth_headers["admin"],
    )

    response = await client.get(
        f"/sensors/{sensor_id}/ai-config",
        headers=auth_headers["operator"],
    )

    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "Sensor AI configuration not found"
    )


@pytest.mark.parametrize(
    "role_name",
    [
        "technician",
        "operator",
    ],
)
async def test_non_management_roles_cannot_create_ai_config(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
    role_name: str,
) -> None:
    sensor_id = await create_test_sensor(
        client,
        auth_headers["admin"],
    )

    response = await client.post(
        f"/sensors/{sensor_id}/ai-config",
        headers=auth_headers[role_name],
        json={
            "is_enabled": True,
            "engine_name": "statistical-zscore",
            "anomaly_threshold": 3.0,
            "min_history": 10,
            "history_limit": 50,
            "high_risk_threshold": 5.0,
            "critical_risk_threshold": 8.0,
        },
    )

    assert response.status_code == 403


async def test_invalid_anomaly_threshold_returns_422(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    sensor_id = await create_test_sensor(
        client,
        auth_headers["admin"],
    )

    response = await client.post(
        f"/sensors/{sensor_id}/ai-config",
        headers=auth_headers["admin"],
        json={
            "is_enabled": True,
            "engine_name": "statistical-zscore",
            "anomaly_threshold": 0,
            "min_history": 10,
            "history_limit": 50,
            "high_risk_threshold": 5.0,
            "critical_risk_threshold": 8.0,
        },
    )

    assert response.status_code == 422


async def test_patch_cannot_make_history_configuration_invalid(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    sensor_id = await create_test_sensor(
        client,
        auth_headers["admin"],
    )

    await create_default_ai_config(
        client,
        auth_headers["admin"],
        sensor_id,
    )

    # Current history_limit is 50.
    # Therefore min_history=100 would make the final
    # configuration invalid.
    response = await client.patch(
        f"/sensors/{sensor_id}/ai-config",
        headers=auth_headers["admin"],
        json={
            "min_history": 100,
        },
    )

    assert response.status_code == 422

    assert (
        response.json()["detail"]
        == "history_limit must be greater than or equal to min_history"
    )


async def test_invalid_risk_threshold_relationship_returns_422(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    sensor_id = await create_test_sensor(
        client,
        auth_headers["admin"],
    )

    response = await client.post(
        f"/sensors/{sensor_id}/ai-config",
        headers=auth_headers["admin"],
        json={
            "is_enabled": True,
            "engine_name": "statistical-zscore",
            "anomaly_threshold": 3.0,
            "min_history": 10,
            "history_limit": 50,
            "high_risk_threshold": 10.0,
            "critical_risk_threshold": 8.0,
        },
    )

    assert response.status_code == 422


async def test_explicit_null_in_ai_config_patch_returns_422(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    sensor_id = await create_test_sensor(
        client,
        auth_headers["admin"],
    )

    await create_default_ai_config(
        client,
        auth_headers["admin"],
        sensor_id,
    )

    response = await client.patch(
        f"/sensors/{sensor_id}/ai-config",
        headers=auth_headers["admin"],
        json={
            "anomaly_threshold": None,
        },
    )

    assert response.status_code == 422