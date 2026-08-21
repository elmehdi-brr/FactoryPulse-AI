from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_roles
from app.core.rbac import ALL_ROLES, MANAGEMENT_ROLES
from app.db.session import get_db
from app.models.user import User
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)
from app.schemas.site import SiteResponse
from app.services.organization_service import (
    create_organization,
    get_organization_by_code,
    get_organization_by_id,
    get_organizations,
    update_organization,
)
from app.services.site_service import get_sites_by_organization


router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"],
)


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_organization_endpoint(
    organization_data: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
) -> OrganizationResponse:
    existing_organization = await get_organization_by_code(
        db,
        organization_data.code,
    )

    if existing_organization is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization code already exists",
        )

    return await create_organization(
        db,
        organization_data,
    )


@router.get(
    "",
    response_model=list[OrganizationResponse],
)
async def get_organizations_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> list[OrganizationResponse]:
    return await get_organizations(db)


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
)
async def get_organization_endpoint(
    organization_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> OrganizationResponse:
    organization = await get_organization_by_id(
        db,
        organization_id,
    )

    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return organization


@router.patch(
    "/{organization_id}",
    response_model=OrganizationResponse,
)
async def update_organization_endpoint(
    organization_id: int,
    organization_data: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
) -> OrganizationResponse:
    organization = await get_organization_by_id(
        db,
        organization_id,
    )

    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    if organization_data.code is not None:
        existing_organization = await get_organization_by_code(
            db,
            organization_data.code,
        )

        if (
            existing_organization is not None
            and existing_organization.id != organization_id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Organization code already exists",
            )

    return await update_organization(
        db,
        organization,
        organization_data,
    )


@router.get(
    "/{organization_id}/sites",
    response_model=list[SiteResponse],
)
async def get_organization_sites_endpoint(
    organization_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> list[SiteResponse]:
    organization = await get_organization_by_id(
        db,
        organization_id,
    )

    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return await get_sites_by_organization(
        db,
        organization_id,
    )