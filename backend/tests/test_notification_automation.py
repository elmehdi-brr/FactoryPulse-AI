from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.alert import Alert
from app.models.notification import Notification
from app.models.role import Role
from app.models.user import User
from app.services.notification_automation_service import (
    create_notifications_for_alert,
)


async def create_notification_test_sensor(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> int:
    organization_response = await client.post(
        "/organizations",
        headers=admin_headers,
        json={
            "name": "Notification Test Industries",
            "code": "NOTIFY-ORG",
            "description": "Notification automation tests",
        },
    )
    assert organization_response.status_code == 201
    organization = organization_response.json()

    site_response = await client.post(
        "/sites",
        headers=admin_headers,
        json={
            "organization_id": organization["id"],
            "name": "Notification Test Factory",
            "code": "NOTIFY-SITE",
            "location": "Test",
            "description": "Notification automation test site",
        },
    )
    assert site_response.status_code == 201
    site = site_response.json()

    area_response = await client.post(
        "/areas",
        headers=admin_headers,
        json={
            "site_id": site["id"],
            "name": "Notification Test Area",
            "code": "NOTIFY-AREA",
            "description": "Notification automation test area",
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
            "name": "Notification Test Machine",
            "code": "NOTIFY-MACHINE",
            "location": "Notification Test Area",
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
            "name": "Notification Test Sensor",
            "sensor_type": "temperature",
            "unit": "celsius",
            "status": "active",
        },
    )

    assert sensor_response.status_code == 201

    return sensor_response.json()["id"]


async def create_anomalous_reading(
    client: AsyncClient,
    admin_headers: dict[str, str],
    sensor_id: int,
) -> None:
    for _ in range(10):
        response = await client.post(
            "/sensor-readings",
            headers=admin_headers,
            json={
                "sensor_id": sensor_id,
                "value": 50.0,
            },
        )

        assert response.status_code == 201

    anomaly_response = await client.post(
        "/sensor-readings",
        headers=admin_headers,
        json={
            "sensor_id": sensor_id,
            "value": 80.0,
        },
    )

    assert anomaly_response.status_code == 201


async def test_ai_alert_notifies_expected_roles(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    sensor_id = await create_notification_test_sensor(
        client,
        auth_headers["admin"],
    )

    await create_anomalous_reading(
        client,
        auth_headers["admin"],
        sensor_id,
    )

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Notification)
            .join(User, Notification.user_id == User.id)
            .join(Role, User.role_id == Role.id)
            .order_by(Role.name)
        )

        notifications = list(result.scalars().all())

        role_result = await db.execute(
            select(Role.name)
            .join(User, User.role_id == Role.id)
            .join(
                Notification,
                Notification.user_id == User.id,
            )
            .order_by(Role.name)
        )

        notified_roles = list(role_result.scalars().all())

    assert len(notifications) == 3
    assert notified_roles == [
        "admin",
        "manager",
        "technician",
    ]

    for notification in notifications:
        assert notification.alert_id is not None
        assert notification.channel == "in_app"
        assert notification.is_read is False


async def test_operator_does_not_receive_automatic_ai_notification(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    sensor_id = await create_notification_test_sensor(
        client,
        auth_headers["admin"],
    )

    await create_anomalous_reading(
        client,
        auth_headers["admin"],
        sensor_id,
    )

    async with AsyncSessionLocal() as db:
        operator_role_result = await db.execute(
            select(Role).where(Role.name == "operator")
        )
        operator_role = operator_role_result.scalar_one()

        operator_result = await db.execute(
            select(User).where(
                User.role_id == operator_role.id
            )
        )
        operator = operator_result.scalar_one()

        notification_result = await db.execute(
            select(Notification).where(
                Notification.user_id == operator.id
            )
        )

        operator_notifications = list(
            notification_result.scalars().all()
        )

    assert operator_notifications == []


async def test_inactive_eligible_user_is_not_notified(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    async with AsyncSessionLocal() as db:
        technician_role_result = await db.execute(
            select(Role).where(Role.name == "technician")
        )
        technician_role = technician_role_result.scalar_one()

        inactive_technician = User(
            email="inactive-technician@test.factorypulse.local",
            full_name="Inactive Test Technician",
            hashed_password=hash_password(
                "inactive-test-password"
            ),
            role_id=technician_role.id,
            is_active=False,
        )

        db.add(inactive_technician)
        await db.commit()
        await db.refresh(inactive_technician)

        inactive_user_id = inactive_technician.id

    sensor_id = await create_notification_test_sensor(
        client,
        auth_headers["admin"],
    )

    await create_anomalous_reading(
        client,
        auth_headers["admin"],
        sensor_id,
    )

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Notification).where(
                Notification.user_id == inactive_user_id
            )
        )

        notifications = list(result.scalars().all())

    assert notifications == []


async def test_notification_generation_is_idempotent(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    sensor_id = await create_notification_test_sensor(
        client,
        auth_headers["admin"],
    )

    await create_anomalous_reading(
        client,
        auth_headers["admin"],
        sensor_id,
    )

    async with AsyncSessionLocal() as db:
        alert_result = await db.execute(
            select(Alert).where(
                Alert.sensor_id == sensor_id
            )
        )

        alert = alert_result.scalar_one()

        existing_result = await db.execute(
            select(Notification).where(
                Notification.alert_id == alert.id
            )
        )

        existing_notifications = list(
            existing_result.scalars().all()
        )

        assert len(existing_notifications) == 3

        created_again = await create_notifications_for_alert(
            db,
            alert,
        )

        assert created_again == []

        final_result = await db.execute(
            select(Notification).where(
                Notification.alert_id == alert.id
            )
        )

        final_notifications = list(
            final_result.scalars().all()
        )

    assert len(final_notifications) == 3