from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.api.dependencies import require_roles
from app.core.rbac import ALL_ROLES, ASSET_WRITE_ROLES, MANAGEMENT_ROLES
from app.db.session import get_db
from app.models.user import User
from app.schemas.machine import MachineCreate, MachineResponse, MachineUpdate
from app.schemas.machine_reliability import MachineReliabilityResponse
from app.services.area_service import get_area_by_id
from app.services.machine_service import (
    create_machine,
    delete_machine,
    get_machine_by_id,
    get_machines,
    update_machine,
)
from app.services.machine_reliability_service import (
    MachineReliabilityServiceError,
    calculate_machine_reliability,
)
from app.services.production_line_service import get_production_line_by_id


router = APIRouter(
    prefix="/machines",
    tags=["Machines"],
)


async def validate_machine_hierarchy(
    db: AsyncSession,
    area_id: int,
    production_line_id: int | None,
) -> None:
    area = await get_area_by_id(
        db,
        area_id,
    )

    if area is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Area not found",
        )

    if production_line_id is None:
        return

    production_line = await get_production_line_by_id(
        db,
        production_line_id,
    )

    if production_line is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production line not found",
        )

    if production_line.area_id != area_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Production line does not belong to the selected area",
        )


@router.post(
    "",
    response_model=MachineResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_machine_endpoint(
    machine_data: MachineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ASSET_WRITE_ROLES)),
) -> MachineResponse:
    await validate_machine_hierarchy(
        db,
        machine_data.area_id,
        machine_data.production_line_id,
    )

    return await create_machine(
        db,
        machine_data,
    )


@router.get(
    "",
    response_model=list[MachineResponse],
)
async def get_machines_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> list[MachineResponse]:
    return await get_machines(db)


@router.get(
    "/{machine_id}",
    response_model=MachineResponse,
)
async def get_machine_endpoint(
    machine_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> MachineResponse:
    machine = await get_machine_by_id(
        db,
        machine_id,
    )

    if machine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found",
        )

    return machine


@router.get(
    "/{machine_id}/reliability",
    response_model=MachineReliabilityResponse,
)
async def get_machine_reliability_endpoint(
    machine_id: int,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> MachineReliabilityResponse:
    machine = await get_machine_by_id(
        db,
        machine_id,
    )

    if machine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found",
        )

    try:
        metrics = await calculate_machine_reliability(
            db,
            machine_id,
            start_at=start_at,
            end_at=end_at,
        )
    except MachineReliabilityServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return MachineReliabilityResponse(
        machine_id=machine_id,
        start_at=start_at,
        end_at=end_at,
        failure_count=metrics.failure_count,
        total_failure_downtime_seconds=(
            metrics.total_failure_downtime_seconds
        ),
        mttr_seconds=metrics.mttr_seconds,
        operating_exposure_seconds=(
            metrics.operating_exposure_seconds
        ),
        mtbf_seconds=metrics.mtbf_seconds,
    )


@router.patch(
    "/{machine_id}",
    response_model=MachineResponse,
)
async def update_machine_endpoint(
    machine_id: int,
    machine_data: MachineUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ASSET_WRITE_ROLES)),
) -> MachineResponse:
    machine = await get_machine_by_id(
        db,
        machine_id,
    )

    if machine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found",
        )

    update_data = machine_data.model_dump(
        exclude_unset=True
    )

    final_area_id = update_data.get(
        "area_id",
        machine.area_id,
    )

    final_production_line_id = update_data.get(
        "production_line_id",
        machine.production_line_id,
    )

    await validate_machine_hierarchy(
        db,
        final_area_id,
        final_production_line_id,
    )

    return await update_machine(
        db,
        machine,
        machine_data,
    )


@router.delete(
    "/{machine_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_machine_endpoint(
    machine_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
) -> None:
    machine = await get_machine_by_id(
        db,
        machine_id,
    )

    if machine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found",
        )

    await delete_machine(
        db,
        machine,
    )