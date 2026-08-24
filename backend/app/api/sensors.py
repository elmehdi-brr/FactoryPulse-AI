from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_roles
from app.core.rbac import (
    ALL_ROLES,
    ASSET_WRITE_ROLES,
    MANAGEMENT_ROLES,
)
from app.db.session import get_db
from app.models.user import User

from app.schemas.sensor import (
    SensorCreate,
    SensorResponse,
    SensorUpdate,
)
from app.schemas.sensor_ai_config import (
    SensorAIConfigCreate,
    SensorAIConfigResponse,
    SensorAIConfigUpdate,
)

from app.services.machine_service import get_machine_by_id
from app.services.sensor_ai_config_service import (
    SensorAIConfigValidationError,
    create_sensor_ai_config,
    get_sensor_ai_config_by_sensor_id,
    update_sensor_ai_config,
)
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


# =========================================================
# SENSOR CRUD
# =========================================================


@router.post(
    "",
    response_model=SensorResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_sensor_endpoint(
    sensor_data: SensorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(*ASSET_WRITE_ROLES)
    ),
) -> SensorResponse:
    machine = await get_machine_by_id(
        db,
        sensor_data.machine_id,
    )

    if machine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found",
        )

    return await create_sensor(
        db,
        sensor_data,
    )


@router.get(
    "",
    response_model=list[SensorResponse],
)
async def get_sensors_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(*ALL_ROLES)
    ),
) -> list[SensorResponse]:
    return await get_sensors(db)


@router.get(
    "/{sensor_id}",
    response_model=SensorResponse,
)
async def get_sensor_endpoint(
    sensor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(*ALL_ROLES)
    ),
) -> SensorResponse:
    sensor = await get_sensor_by_id(
        db,
        sensor_id,
    )

    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found",
        )

    return sensor


# =========================================================
# SENSOR AI CONFIGURATION
# =========================================================


@router.post(
    "/{sensor_id}/ai-config",
    response_model=SensorAIConfigResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_sensor_ai_config_endpoint(
    sensor_id: int,
    config_data: SensorAIConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
) -> SensorAIConfigResponse:
    sensor = await get_sensor_by_id(
        db,
        sensor_id,
    )

    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found",
        )

    existing_config = await get_sensor_ai_config_by_sensor_id(
        db,
        sensor_id,
    )

    if existing_config is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sensor AI configuration already exists",
        )

    return await create_sensor_ai_config(
        db,
        sensor_id,
        config_data,
    )


@router.get(
    "/{sensor_id}/ai-config",
    response_model=SensorAIConfigResponse,
)
async def get_sensor_ai_config_endpoint(
    sensor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(*ALL_ROLES)
    ),
) -> SensorAIConfigResponse:
    sensor = await get_sensor_by_id(
        db,
        sensor_id,
    )

    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found",
        )

    config = await get_sensor_ai_config_by_sensor_id(
        db,
        sensor_id,
    )

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor AI configuration not found",
        )

    return config


@router.patch(
    "/{sensor_id}/ai-config",
    response_model=SensorAIConfigResponse,
)
async def update_sensor_ai_config_endpoint(
    sensor_id: int,
    config_data: SensorAIConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
) -> SensorAIConfigResponse:
    sensor = await get_sensor_by_id(
        db,
        sensor_id,
    )

    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found",
        )

    config = await get_sensor_ai_config_by_sensor_id(
        db,
        sensor_id,
    )

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor AI configuration not found",
        )

    try:
        return await update_sensor_ai_config(
            db,
            config,
            config_data,
        )
    except SensorAIConfigValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


# =========================================================
# SENSOR UPDATE / DELETE
# =========================================================


@router.patch(
    "/{sensor_id}",
    response_model=SensorResponse,
)
async def update_sensor_endpoint(
    sensor_id: int,
    sensor_data: SensorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(*ASSET_WRITE_ROLES)
    ),
) -> SensorResponse:
    sensor = await get_sensor_by_id(
        db,
        sensor_id,
    )

    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found",
        )

    if sensor_data.machine_id is not None:
        machine = await get_machine_by_id(
            db,
            sensor_data.machine_id,
        )

        if machine is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Machine not found",
            )

    return await update_sensor(
        db,
        sensor,
        sensor_data,
    )


@router.delete(
    "/{sensor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_sensor_endpoint(
    sensor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGEMENT_ROLES)
    ),
) -> None:
    sensor = await get_sensor_by_id(
        db,
        sensor_id,
    )

    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found",
        )

    await delete_sensor(
        db,
        sensor,
    )