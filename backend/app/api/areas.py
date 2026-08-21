from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_roles
from app.core.rbac import ALL_ROLES, MANAGEMENT_ROLES
from app.db.session import get_db
from app.models.user import User
from app.schemas.area import (
    AreaCreate,
    AreaResponse,
    AreaUpdate,
)
from app.schemas.machine import MachineResponse
from app.schemas.production_line import ProductionLineResponse
from app.services.area_service import (
    create_area,
    get_area_by_code,
    get_area_by_id,
    get_areas,
    update_area,
)
from app.services.site_service import get_site_by_id
from app.services.machine_service import get_machines_by_area
from app.services.production_line_service import get_production_lines_by_area


router = APIRouter(
    prefix="/areas",
    tags=["Areas"],
)


@router.post(
    "",
    response_model=AreaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_area_endpoint(
    area_data: AreaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
) -> AreaResponse:
    site = await get_site_by_id(
        db,
        area_data.site_id,
    )

    if site is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found",
        )

    existing_area = await get_area_by_code(
        db,
        area_data.code,
    )

    if existing_area is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Area code already exists",
        )

    return await create_area(
        db,
        area_data,
    )


@router.get(
    "",
    response_model=list[AreaResponse],
)
async def get_areas_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> list[AreaResponse]:
    return await get_areas(db)


@router.get(
    "/{area_id}",
    response_model=AreaResponse,
)
async def get_area_endpoint(
    area_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> AreaResponse:
    area = await get_area_by_id(
        db,
        area_id,
    )

    if area is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Area not found",
        )

    return area


@router.patch(
    "/{area_id}",
    response_model=AreaResponse,
)
async def update_area_endpoint(
    area_id: int,
    area_data: AreaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
) -> AreaResponse:
    area = await get_area_by_id(
        db,
        area_id,
    )

    if area is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Area not found",
        )

    if area_data.site_id is not None:
        site = await get_site_by_id(
            db,
            area_data.site_id,
        )

        if site is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Site not found",
            )

    if area_data.code is not None:
        existing_area = await get_area_by_code(
            db,
            area_data.code,
        )

        if (
            existing_area is not None
            and existing_area.id != area_id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Area code already exists",
            )

    return await update_area(
        db,
        area,
        area_data,
    )

@router.get(
    "/{area_id}/production-lines",
    response_model=list[ProductionLineResponse],
)
async def get_area_production_lines_endpoint(
    area_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> list[ProductionLineResponse]:
    area = await get_area_by_id(
        db,
        area_id,
    )

    if area is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Area not found",
        )

    return await get_production_lines_by_area(
        db,
        area_id,
    )


@router.get(
    "/{area_id}/machines",
    response_model=list[MachineResponse],
)
async def get_area_machines_endpoint(
    area_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> list[MachineResponse]:
    area = await get_area_by_id(
        db,
        area_id,
    )

    if area is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Area not found",
        )

    return await get_machines_by_area(
        db,
        area_id,
    )