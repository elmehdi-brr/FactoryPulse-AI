import pytest
from httpx import AsyncClient


async def get_user_id(
    client: AsyncClient,
    headers: dict[str, str],
) -> int:
    response = await client.get(
        "/auth/me",
        headers=headers,
    )

    assert response.status_code == 200
    return response.json()["id"]


async def create_test_notification(
    client: AsyncClient,
    admin_headers: dict[str, str],
    user_id: int,
) -> dict:
    response = await client.post(
        "/notifications",
        headers=admin_headers,
        json={
            "user_id": user_id,
            "title": "Notification permission test",
            "message": "Testing notification ownership.",
            "channel": "in_app",
            "is_read": False,
        },
    )

    assert response.status_code == 201, response.text
    return response.json()


async def get_notification_by_id(
    notifications: list[dict],
    notification_id: int,
) -> dict:
    return next(
        notification
        for notification in notifications
        if notification["id"] == notification_id
    )


async def test_user_can_read_and_update_own_notification(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    operator_headers = auth_headers["operator"]

    operator_id = await get_user_id(
        client,
        operator_headers,
    )

    created = await create_test_notification(
        client,
        auth_headers["admin"],
        operator_id,
    )

    notification_id = created["id"]

    response = await client.get(
        f"/users/{operator_id}/notifications",
        headers=operator_headers,
    )

    assert response.status_code == 200

    notification = await get_notification_by_id(
        response.json(),
        notification_id,
    )
    assert notification["is_read"] is False

    update_response = await client.patch(
        f"/notifications/{notification_id}",
        headers=operator_headers,
        json={"is_read": True},
    )

    assert update_response.status_code == 200
    assert update_response.json()["is_read"] is True

    refreshed_response = await client.get(
        f"/users/{operator_id}/notifications",
        headers=operator_headers,
    )

    assert refreshed_response.status_code == 200

    refreshed_notification = await get_notification_by_id(
        refreshed_response.json(),
        notification_id,
    )

    assert refreshed_notification["is_read"] is True


@pytest.mark.parametrize(
    "role_name",
    ["operator", "technician"],
)
async def test_non_management_user_cannot_access_another_users_notification(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
    role_name: str,
) -> None:
    target_id = await get_user_id(
        client,
        auth_headers["manager"],
    )

    notification = await create_test_notification(
        client,
        auth_headers["admin"],
        target_id,
    )

    notification_id = notification["id"]
    headers = auth_headers[role_name]

    list_response = await client.get(
        f"/users/{target_id}/notifications",
        headers=headers,
    )

    assert list_response.status_code == 403

    detail_response = await client.get(
        f"/notifications/{notification_id}",
        headers=headers,
    )

    assert detail_response.status_code == 403

    update_response = await client.patch(
        f"/notifications/{notification_id}",
        headers=headers,
        json={"is_read": True},
    )

    assert update_response.status_code == 403


async def test_manager_can_access_another_users_notification(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    operator_id = await get_user_id(
        client,
        auth_headers["operator"],
    )

    notification = await create_test_notification(
        client,
        auth_headers["admin"],
        operator_id,
    )

    notification_id = notification["id"]

    list_response = await client.get(
        f"/users/{operator_id}/notifications",
        headers=auth_headers["manager"],
    )

    assert list_response.status_code == 200

    notification_from_list = await get_notification_by_id(
        list_response.json(),
        notification_id,
    )

    assert notification_from_list["user_id"] == operator_id

    detail_response = await client.get(
        f"/notifications/{notification_id}",
        headers=auth_headers["manager"],
    )

    assert detail_response.status_code == 200

    update_response = await client.patch(
        f"/notifications/{notification_id}",
        headers=auth_headers["manager"],
        json={"is_read": True},
    )

    assert update_response.status_code == 200
    assert update_response.json()["is_read"] is True


async def test_notification_endpoints_require_authentication(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    user_id = await get_user_id(
        client,
        auth_headers["operator"],
    )

    notification = await create_test_notification(
        client,
        auth_headers["admin"],
        user_id,
    )

    notification_id = notification["id"]

    list_response = await client.get(
        f"/users/{user_id}/notifications",
    )

    assert list_response.status_code == 401

    detail_response = await client.get(
        f"/notifications/{notification_id}",
    )

    assert detail_response.status_code == 401

    update_response = await client.patch(
        f"/notifications/{notification_id}",
        json={"is_read": True},
    )

    assert update_response.status_code == 401