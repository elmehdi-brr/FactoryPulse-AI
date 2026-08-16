from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.alert import AlertCreate, AlertResponse, AlertUpdate
from app.services.alert_service import (
    create_alert,
    get_alert_by_id,
    get_alerts,
    get_alerts_by_sensor,
    update_alert,
)
from app.services.prediction_service import get_prediction_by_id
from app.services.sensor_service import get_sensor_by_id


router = APIRouter(
    tags=["Alerts"],
)


@router.post(
    "/alerts",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_alert_endpoint(
    alert_data: AlertCreate,
    db: AsyncSession = Depends(get_db),
) -> AlertResponse:
    sensor = await get_sensor_by_id(db, alert_data.sensor_id)

    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found",
        )

    if alert_data.prediction_id is not None:
        prediction = await get_prediction_by_id(
            db,
            alert_data.prediction_id,
        )

        if prediction is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prediction not found",
            )

        if prediction.sensor_id != alert_data.sensor_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prediction does not belong to the specified sensor",
            )

    return await create_alert(db, alert_data)


@router.get(
    "/alerts",
    response_model=list[AlertResponse],
)
async def get_alerts_endpoint(
    db: AsyncSession = Depends(get_db),
) -> list[AlertResponse]:
    return await get_alerts(db)


@router.get(
    "/alerts/{alert_id}",
    response_model=AlertResponse,
)
async def get_alert_endpoint(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
) -> AlertResponse:
    alert = await get_alert_by_id(db, alert_id)

    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    return alert


@router.get(
    "/sensors/{sensor_id}/alerts",
    response_model=list[AlertResponse],
)
async def get_sensor_alerts_endpoint(
    sensor_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[AlertResponse]:
    sensor = await get_sensor_by_id(db, sensor_id)

    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found",
        )

    return await get_alerts_by_sensor(db, sensor_id)


@router.patch(
    "/alerts/{alert_id}",
    response_model=AlertResponse,
)
async def update_alert_endpoint(
    alert_id: int,
    alert_data: AlertUpdate,
    db: AsyncSession = Depends(get_db),
) -> AlertResponse:
    alert = await get_alert_by_id(db, alert_id)

    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    return await update_alert(db, alert, alert_data)