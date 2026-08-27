from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_roles
from app.core.rbac import ALL_ROLES, ASSET_WRITE_ROLES
from app.db.session import get_db
from app.models.user import User
from app.schemas.production_run import (
    ProductionRunCreate,
    ProductionRunResponse,
    ProductionRunUpdate,
)
from app.schemas.oee import OEEResponse
from app.services.production_line_service import (
    get_production_line_by_id,
)
from app.services.production_run_service import (
    ProductionRunValidationError,
    create_production_run,
    get_production_run_by_id,
    get_production_runs,
    get_production_runs_by_line,
    update_production_run,
    ProductionRunValidationError,
)
from app.services.oee_service import (
    OEEServiceError,
    calculate_production_run_oee,
)


router = APIRouter(
    tags=["Production Runs"],
)


@router.post(
    "/production-runs",
    response_model=ProductionRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_production_run_endpoint(
    run_data: ProductionRunCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(*ASSET_WRITE_ROLES)
    ),
) -> ProductionRunResponse:
    production_line = await get_production_line_by_id(
        db,
        run_data.production_line_id,
    )

    if production_line is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production line not found",
        )

    try:
        return await create_production_run(
            db,
            run_data,
        )
    except ProductionRunValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.get(
    "/production-runs",
    response_model=list[ProductionRunResponse],
)
async def get_production_runs_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(*ALL_ROLES)
    ),
) -> list[ProductionRunResponse]:
    return await get_production_runs(db)


@router.get(
    "/production-runs/{production_run_id}",
    response_model=ProductionRunResponse,
)
async def get_production_run_endpoint(
    production_run_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(*ALL_ROLES)
    ),
) -> ProductionRunResponse:
    production_run = await get_production_run_by_id(
        db,
        production_run_id,
    )

    if production_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production run not found",
        )

    return production_run


@router.get(
    "/production-runs/{production_run_id}/oee",
    response_model=OEEResponse,
)
async def get_production_run_oee_endpoint(
    production_run_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(*ALL_ROLES)
    ),
) -> OEEResponse:
    production_run = await get_production_run_by_id(
        db,
        production_run_id,
    )

    if production_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production run not found",
        )

    try:
        metrics = await calculate_production_run_oee(
            db,
            production_run,
        )
    except OEEServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return OEEResponse(
        production_run_id=production_run.id,
        scheduled_time_seconds=(
            metrics.scheduled_time_seconds
        ),
        planned_downtime_seconds=(
            metrics.planned_downtime_seconds
        ),
        planned_production_time_seconds=(
            metrics.planned_production_time_seconds
        ),
        unplanned_downtime_seconds=(
            metrics.unplanned_downtime_seconds
        ),
        operating_time_seconds=(
            metrics.operating_time_seconds
        ),
        availability=metrics.availability,
        performance=metrics.performance,
        quality=metrics.quality,
        oee=metrics.oee,
    )


@router.patch(
    "/production-runs/{production_run_id}",
    response_model=ProductionRunResponse,
)
async def update_production_run_endpoint(
    production_run_id: int,
    run_data: ProductionRunUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(*ASSET_WRITE_ROLES)
    ),
) -> ProductionRunResponse:
    production_run = await get_production_run_by_id(
        db,
        production_run_id,
    )

    if production_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production run not found",
        )

    try:
        return await update_production_run(
            db,
            production_run,
            run_data,
        )
    except ProductionRunValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.get(
    "/production-lines/{production_line_id}/production-runs",
    response_model=list[ProductionRunResponse],
)
async def get_production_line_runs_endpoint(
    production_line_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(*ALL_ROLES)
    ),
) -> list[ProductionRunResponse]:
    production_line = await get_production_line_by_id(
        db,
        production_line_id,
    )

    if production_line is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production line not found",
        )

    return await get_production_runs_by_line(
        db,
        production_line_id,
    )