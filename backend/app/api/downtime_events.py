from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_roles
from app.core.rbac import ALL_ROLES, READING_WRITE_ROLES
from app.db.session import get_db
from app.models.user import User
from app.schemas.downtime_event import (
    DowntimeEventCreate,
    DowntimeEventResponse,
    DowntimeEventUpdate,
)
from app.services.downtime_event_service import (
    DowntimeEventValidationError,
    create_downtime_event,
    get_downtime_event_by_id,
    get_downtime_events,
    get_downtime_events_by_run,
    update_downtime_event,
    validate_downtime_timing,
    validate_machine_for_production_run,
)
from app.services.production_run_service import (
    get_production_run_by_id,
)


router = APIRouter(
    tags=["Downtime Events"],
)


@router.post(
    "/downtime-events",
    response_model=DowntimeEventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_downtime_event_endpoint(
    downtime_data: DowntimeEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(*READING_WRITE_ROLES)
    ),
) -> DowntimeEventResponse:
    production_run = await get_production_run_by_id(
        db,
        downtime_data.production_run_id,
    )

    if production_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production run not found",
        )

    try:
        await validate_machine_for_production_run(
            db,
            production_run,
            downtime_data.machine_id,
        )
    except DowntimeEventValidationError as exc:
        if str(exc) == "Machine not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Machine not found",
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    try:
        validate_downtime_timing(
            production_run,
            downtime_data,
        )
    except DowntimeEventValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return await create_downtime_event(
        db,
        downtime_data,
    )


@router.get(
    "/downtime-events",
    response_model=list[DowntimeEventResponse],
)
async def get_downtime_events_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(*ALL_ROLES)
    ),
) -> list[DowntimeEventResponse]:
    return await get_downtime_events(db)


@router.get(
    "/downtime-events/{downtime_event_id}",
    response_model=DowntimeEventResponse,
)
async def get_downtime_event_endpoint(
    downtime_event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(*ALL_ROLES)
    ),
) -> DowntimeEventResponse:
    downtime_event = await get_downtime_event_by_id(
        db,
        downtime_event_id,
    )

    if downtime_event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Downtime event not found",
        )

    return downtime_event


@router.patch(
    "/downtime-events/{downtime_event_id}",
    response_model=DowntimeEventResponse,
)
async def update_downtime_event_endpoint(
    downtime_event_id: int,
    downtime_data: DowntimeEventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(*READING_WRITE_ROLES)
    ),
) -> DowntimeEventResponse:
    downtime_event = await get_downtime_event_by_id(
        db,
        downtime_event_id,
    )

    if downtime_event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Downtime event not found",
        )

    production_run = await get_production_run_by_id(
        db,
        downtime_event.production_run_id,
    )

    if production_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production run not found",
        )

    try:
        return await update_downtime_event(
            db,
            downtime_event,
            production_run,
            downtime_data,
        )
    except DowntimeEventValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.get(
    "/production-runs/{production_run_id}/downtime-events",
    response_model=list[DowntimeEventResponse],
)
async def get_production_run_downtime_events_endpoint(
    production_run_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(*ALL_ROLES)
    ),
) -> list[DowntimeEventResponse]:
    production_run = await get_production_run_by_id(
        db,
        production_run_id,
    )

    if production_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production run not found",
        )

    return await get_downtime_events_by_run(
        db,
        production_run_id,
    )