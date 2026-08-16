from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
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

    return await create_notification(db, notification_data)


@router.get(
    "/notifications",
    response_model=list[NotificationResponse],
)
async def get_notifications_endpoint(
    db: AsyncSession = Depends(get_db),
) -> list[NotificationResponse]:
    return await get_notifications(db)


@router.get(
    "/notifications/{notification_id}",
    response_model=NotificationResponse,
)
async def get_notification_endpoint(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
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

    return notification


@router.get(
    "/users/{user_id}/notifications",
    response_model=list[NotificationResponse],
)
async def get_user_notifications_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[NotificationResponse]:
    user = await get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
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

    return await update_notification(
        db,
        notification,
        notification_data,
    )