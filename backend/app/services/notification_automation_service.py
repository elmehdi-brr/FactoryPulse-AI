from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import RoleName
from app.models.alert import Alert
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate
from app.services.notification_service import (
    create_notifications,
    get_notified_user_ids_for_alert,
)
from app.services.user_service import get_active_users_by_roles


AUTO_ALERT_RECIPIENT_ROLES = (
    RoleName.ADMIN.value,
    RoleName.MANAGER.value,
    RoleName.TECHNICIAN.value,
)


async def create_notifications_for_alert(
    db: AsyncSession,
    alert: Alert,
) -> list[Notification]:
    recipients = await get_active_users_by_roles(
        db,
        AUTO_ALERT_RECIPIENT_ROLES,
    )

    already_notified_user_ids = (
        await get_notified_user_ids_for_alert(
            db,
            alert.id,
        )
    )

    notification_data = [
        NotificationCreate(
            user_id=user.id,
            alert_id=alert.id,
            title=f"[{alert.severity.upper()}] {alert.title}",
            message=alert.message,
            channel="in_app",
            is_read=False,
        )
        for user in recipients
        if user.id not in already_notified_user_ids
    ]

    return await create_notifications(
        db,
        notification_data,
    )