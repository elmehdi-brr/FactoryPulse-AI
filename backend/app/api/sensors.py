from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_roles
from app.core.rbac import ALL_ROLES, ASSET_WRITE_ROLES, MANAGEMENT_ROLES
from app.db.session import get_db
from app.models.user import User
from app.schemas.sensor import SensorCreate, SensorResponse, SensorUpdate
from app.services.machine_service import get_machine_by_id
from app.services.sensor_service import (
    create_sensor,
    delete_sensor,
    get_sensor_by_id,
    get_sensors,
    update_sensor,
)


router = APIRouter(
    prefix="/sensors",
    tags=["Sensors"],
)


@router.post(
    "",
    response_model=SensorResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_sensor_endpoint(
    sensor_data: SensorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ASSET_WRITE_ROLES)),
) -> SensorResponse:
    machine = await get_machine_by_id(db, sensor_data.machine_id)

    if machine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found",
        )

    return await create_sensor(db, sensor_data)


@router.get(
    "",
    response_model=list[SensorResponse],
)
async def get_sensors_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> list[SensorResponse]:
    return await get_sensors(db)


@router.get(
    "/{sensor_id}",
    response_model=SensorResponse,
)
async def get_sensor_endpoint(
    sensor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> SensorResponse:
    sensor = await get_sensor_by_id(db, sensor_id)

    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found",
        )

    return sensor


@router.patch(
    "/{sensor_id}",
    response_model=SensorResponse,
)
async def update_sensor_endpoint(
    sensor_id: int,
    sensor_data: SensorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ASSET_WRITE_ROLES)),
) -> SensorResponse:
    sensor = await get_sensor_by_id(db, sensor_id)

    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found",
        )

    if sensor_data.machine_id is not None:
        machine = await get_machine_by_id(db, sensor_data.machine_id)

        if machine is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Machine not found",
            )

    return await update_sensor(db, sensor, sensor_data)


@router.delete(
    "/{sensor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_sensor_endpoint(
    sensor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
) -> None:
    sensor = await get_sensor_by_id(db, sensor_id)

    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found",
        )

    await delete_sensor(db, sensor)