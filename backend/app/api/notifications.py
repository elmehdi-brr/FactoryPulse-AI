from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import require_roles, user_has_any_role
from app.core.rbac import ALL_ROLES, MANAGEMENT_ROLES
from app.db.session import get_db
from app.models.user import User
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationUpdate,
)
from app.services.alert_service import get_alert_by_id
from app.services.notification_service import (
    create_notification,
    get_notification_by_id,
    get_notifications,
    get_notification_by_user_alert_channel,
    get_notifications_by_user,
    update_notification,
)
from app.services.user_service import get_user_by_id


router = APIRouter(
    tags=["Notifications"],
)


@router.post(
    "/notifications",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_notification_endpoint(
    notification_data: NotificationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
) -> NotificationResponse:
    user = await get_user_by_id(db, notification_data.user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if notification_data.alert_id is not None:
        alert = await get_alert_by_id(
            db,
            notification_data.alert_id,
        )

        if alert is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found",
            )
        existing_notification = (
            await get_notification_by_user_alert_channel(
                db,
                user_id=notification_data.user_id,
                alert_id=notification_data.alert_id,
                channel=notification_data.channel,
            )
        )

        if existing_notification is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Notification already exists for this user, "
                    "alert, and channel"
                ),
            )

    try:
        return await create_notification(
            db,
            notification_data,
        )
    except IntegrityError:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Notification already exists for this user, "
                "alert, and channel"
            ),
        )


@router.get(
    "/notifications",
    response_model=list[NotificationResponse],
)
async def get_notifications_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
) -> list[NotificationResponse]:
    return await get_notifications(db)


@router.get(
    "/notifications/{notification_id}",
    response_model=NotificationResponse,
)
async def get_notification_endpoint(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> NotificationResponse:
    notification = await get_notification_by_id(
        db,
        notification_id,
    )

    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    is_management = await user_has_any_role(
        db,
        current_user,
        *MANAGEMENT_ROLES,
    )

    if notification.user_id != current_user.id and not is_management:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access this notification",
        )

    return notification


@router.get(
    "/users/{user_id}/notifications",
    response_model=list[NotificationResponse],
)
async def get_user_notifications_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> list[NotificationResponse]:
    user = await get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    is_management = await user_has_any_role(
        db,
        current_user,
        *MANAGEMENT_ROLES,
    )

    if current_user.id != user_id and not is_management:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access another user's notifications",
        )

    return await get_notifications_by_user(db, user_id)


@router.patch(
    "/notifications/{notification_id}",
    response_model=NotificationResponse,
)
async def update_notification_endpoint(
    notification_id: int,
    notification_data: NotificationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> NotificationResponse:
    notification = await get_notification_by_id(
        db,
        notification_id,
    )

    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    is_management = await user_has_any_role(
        db,
        current_user,
        *MANAGEMENT_ROLES,
    )

    if notification.user_id != current_user.id and not is_management:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot modify this notification",
        )

    return await update_notification(
        db,
        notification,
        notification_data,
    )