from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_roles
from app.core.rbac import ALL_ROLES, READING_WRITE_ROLES
from app.db.session import get_db
from app.models.user import User
from app.schemas.sensor_reading import SensorReadingCreate, SensorReadingResponse
from app.services.sensor_reading_service import (
    create_sensor_reading,
    get_readings_by_sensor,
    get_sensor_reading_by_id,
    get_sensor_readings,
)
from app.services.sensor_service import get_sensor_by_id


router = APIRouter(
    tags=["Sensor Readings"],
)


@router.post(
    "/sensor-readings",
    response_model=SensorReadingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_sensor_reading_endpoint(
    reading_data: SensorReadingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*READING_WRITE_ROLES)),
) -> SensorReadingResponse:
    sensor = await get_sensor_by_id(db, reading_data.sensor_id)

    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found",
        )

    return await create_sensor_reading(db, reading_data)


@router.get(
    "/sensor-readings",
    response_model=list[SensorReadingResponse],
)
async def get_sensor_readings_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> list[SensorReadingResponse]:
    return await get_sensor_readings(db)


@router.get(
    "/sensor-readings/{reading_id}",
    response_model=SensorReadingResponse,
)
async def get_sensor_reading_endpoint(
    reading_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> SensorReadingResponse:
    reading = await get_sensor_reading_by_id(db, reading_id)

    if reading is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor reading not found",
        )

    return reading


@router.get(
    "/sensors/{sensor_id}/readings",
    response_model=list[SensorReadingResponse],
)
async def get_sensor_readings_by_sensor_endpoint(
    sensor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> list[SensorReadingResponse]:
    sensor = await get_sensor_by_id(db, sensor_id)

    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found",
        )

    return await get_readings_by_sensor(db, sensor_id)