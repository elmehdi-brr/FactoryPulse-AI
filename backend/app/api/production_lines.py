from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_roles
from app.core.rbac import ALL_ROLES, MANAGEMENT_ROLES
from app.db.session import get_db
from app.models.user import User
from app.schemas.production_line import (
    ProductionLineCreate,
    ProductionLineResponse,
    ProductionLineUpdate,
)
from app.services.area_service import get_area_by_id
from app.services.production_line_service import (
    create_production_line,
    get_production_line_by_code,
    get_production_line_by_id,
    get_production_lines,
    update_production_line,
)


router = APIRouter(
    prefix="/production-lines",
    tags=["Production Lines"],
)


@router.post(
    "",
    response_model=ProductionLineResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_production_line_endpoint(
    line_data: ProductionLineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
) -> ProductionLineResponse:
    area = await get_area_by_id(
        db,
        line_data.area_id,
    )

    if area is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Area not found",
        )

    existing_line = await get_production_line_by_code(
        db,
        line_data.code,
    )

    if existing_line is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Production line code already exists",
        )

    return await create_production_line(
        db,
        line_data,
    )


@router.get(
    "",
    response_model=list[ProductionLineResponse],
)
async def get_production_lines_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> list[ProductionLineResponse]:
    return await get_production_lines(db)


@router.get(
    "/{production_line_id}",
    response_model=ProductionLineResponse,
)
async def get_production_line_endpoint(
    production_line_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> ProductionLineResponse:
    production_line = await get_production_line_by_id(
        db,
        production_line_id,
    )

    if production_line is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production line not found",
        )

    return production_line


@router.patch(
    "/{production_line_id}",
    response_model=ProductionLineResponse,
)
async def update_production_line_endpoint(
    production_line_id: int,
    line_data: ProductionLineUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
) -> ProductionLineResponse:
    production_line = await get_production_line_by_id(
        db,
        production_line_id,
    )

    if production_line is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Production line not found",
        )

    if line_data.area_id is not None:
        area = await get_area_by_id(
            db,
            line_data.area_id,
        )

        if area is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Area not found",
            )

    if line_data.code is not None:
        existing_line = await get_production_line_by_code(
            db,
            line_data.code,
        )

        if (
            existing_line is not None
            and existing_line.id != production_line_id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Production line code already exists",
            )

    return await update_production_line(
        db,
        production_line,
        line_data,
    )