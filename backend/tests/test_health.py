from httpx import AsyncClient

from app.core.config import settings


async def test_test_environment_is_active() -> None:
    assert settings.environment == "test"
    assert settings.database_url.endswith(
        "/factorypulse_test"
    )


async def test_health_endpoint(
    client: AsyncClient,
) -> None:
    response = await client.get("/health")

    assert response.status_code == 200