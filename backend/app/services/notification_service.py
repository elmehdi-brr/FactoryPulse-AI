from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationUpdate


async def create_notification(
    db: AsyncSession,
    notification_data: NotificationCreate,
) -> Notification:
    notification = Notification(**notification_data.model_dump())

    db.add(notification)
    await db.commit()
    await db.refresh(notification)

    return notification


async def get_notification_by_id(
    db: AsyncSession,
    notification_id: int,
) -> Notification | None:
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )

    return result.scalar_one_or_none()


async def get_notifications(
    db: AsyncSession,
) -> list[Notification]:
    result = await db.execute(
        select(Notification).order_by(Notification.created_at.desc())
    )

    return list(result.scalars().all())


async def get_notifications_by_user(
    db: AsyncSession,
    user_id: int,
) -> list[Notification]:
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
    )

    return list(result.scalars().all())


async def update_notification(
    db: AsyncSession,
    notification: Notification,
    notification_data: NotificationUpdate,
) -> Notification:
    update_data = notification_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(notification, field, value)

    await db.commit()
    await db.refresh(notification)

    return notification


async def get_notified_user_ids_for_alert(
    db: AsyncSession,
    alert_id: int,
) -> set[int]:
    result = await db.execute(
        select(Notification.user_id).where(
            Notification.alert_id == alert_id
        )
    )

    return set(result.scalars().all())


async def create_notifications(
    db: AsyncSession,
    notifications_data: list[NotificationCreate],
) -> list[Notification]:
    if not notifications_data:
        return []

    notifications = [
        Notification(**notification_data.model_dump())
        for notification_data in notifications_data
    ]

    db.add_all(notifications)

    await db.commit()

    for notification in notifications:
        await db.refresh(notification)

    return notifications