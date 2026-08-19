from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_roles
from app.core.rbac import RoleName
from app.db.session import get_db
from app.models.user import User
from app.schemas.role import RoleResponse
from app.services.role_service import (
    get_role_by_id,
    get_roles,
)


router = APIRouter(
    prefix="/roles",
    tags=["Roles"],
)


@router.get(
    "",
    response_model=list[RoleResponse],
)
async def get_roles_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(RoleName.ADMIN)
    ),
) -> list[RoleResponse]:
    return await get_roles(db)


@router.get(
    "/{role_id}",
    response_model=RoleResponse,
)
async def get_role_endpoint(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(RoleName.ADMIN)
    ),
) -> RoleResponse:
    role = await get_role_by_id(db, role_id)

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    return role