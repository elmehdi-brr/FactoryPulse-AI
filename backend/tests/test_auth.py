import pytest
from httpx import AsyncClient


@pytest.mark.parametrize(
    ("role_name", "expected_email", "expected_full_name"),
    [
        (
            "admin",
            "admin@test.factorypulse.local",
            "Test Administrator",
        ),
        (
            "manager",
            "manager@test.factorypulse.local",
            "Test Manager",
        ),
        (
            "technician",
            "technician@test.factorypulse.local",
            "Test Technician",
        ),
        (
            "operator",
            "operator@test.factorypulse.local",
            "Test Operator",
        ),
    ],
)
async def test_auth_me_returns_current_user_with_role_name(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
    role_name: str,
    expected_email: str,
    expected_full_name: str,
) -> None:
    response = await client.get(
        "/auth/me",
        headers=auth_headers[role_name],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == expected_email
    assert data["full_name"] == expected_full_name

    assert isinstance(data["id"], int)
    assert isinstance(data["role_id"], int)

    assert data["role_name"] == role_name

    assert data["is_active"] is True
    assert isinstance(data["created_at"], str)


async def test_auth_me_requires_authentication(
    client: AsyncClient,
) -> None:
    response = await client.get(
        "/auth/me"
    )

    assert response.status_code == 401