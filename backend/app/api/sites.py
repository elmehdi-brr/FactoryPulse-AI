from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_roles
from app.core.rbac import ALL_ROLES, MANAGEMENT_ROLES
from app.db.session import get_db
from app.models.user import User
from app.schemas.site import (
    SiteCreate,
    SiteResponse,
    SiteUpdate,
)
from app.schemas.area import AreaResponse
from app.services.area_service import get_areas_by_site
from app.services.organization_service import get_organization_by_id
from app.services.site_service import (
    create_site,
    get_site_by_code,
    get_site_by_id,
    get_sites,
    update_site,
)


router = APIRouter(
    prefix="/sites",
    tags=["Sites"],
)


@router.post(
    "",
    response_model=SiteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_site_endpoint(
    site_data: SiteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
) -> SiteResponse:
    organization = await get_organization_by_id(
        db,
        site_data.organization_id,
    )

    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    existing_site = await get_site_by_code(
        db,
        site_data.code,
    )

    if existing_site is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Site code already exists",
        )

    return await create_site(
        db,
        site_data,
    )


@router.get(
    "",
    response_model=list[SiteResponse],
)
async def get_sites_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> list[SiteResponse]:
    return await get_sites(db)


@router.get(
    "/{site_id}",
    response_model=SiteResponse,
)
async def get_site_endpoint(
    site_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> SiteResponse:
    site = await get_site_by_id(
        db,
        site_id,
    )

    if site is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found",
        )

    return site


@router.patch(
    "/{site_id}",
    response_model=SiteResponse,
)
async def update_site_endpoint(
    site_id: int,
    site_data: SiteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
) -> SiteResponse:
    site = await get_site_by_id(
        db,
        site_id,
    )

    if site is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found",
        )

    if site_data.organization_id is not None:
        organization = await get_organization_by_id(
            db,
            site_data.organization_id,
        )

        if organization is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

    if site_data.code is not None:
        existing_site = await get_site_by_code(
            db,
            site_data.code,
        )

        if (
            existing_site is not None
            and existing_site.id != site_id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Site code already exists",
            )

    return await update_site(
        db,
        site,
        site_data,
    )

@router.get(
    "/{site_id}/areas",
    response_model=list[AreaResponse],
)
async def get_site_areas_endpoint(
    site_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> list[AreaResponse]:
    site = await get_site_by_id(
        db,
        site_id,
    )

    if site is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found",
        )

    return await get_areas_by_site(
        db,
        site_id,
    )