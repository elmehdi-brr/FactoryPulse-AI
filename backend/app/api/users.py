from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_roles
from app.core.rbac import RoleName
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.role_service import get_role_by_id
from app.services.user_service import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_users,
    update_user,
)


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "",
    response_model=list[UserResponse],
)
async def get_users_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(RoleName.ADMIN)
    ),
) -> list[UserResponse]:
    return await get_users(db)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user_endpoint(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(RoleName.ADMIN)
    ),
) -> UserResponse:
    existing_user = await get_user_by_email(
        db,
        user_data.email,
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    if user_data.role_id is not None:
        role = await get_role_by_id(
            db,
            user_data.role_id,
        )

        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )

    return await create_user(db, user_data)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
async def get_user_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(RoleName.ADMIN)
    ),
) -> UserResponse:
    user = await get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
)
async def update_user_endpoint(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(RoleName.ADMIN)
    ),
) -> UserResponse:
    user = await get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user_data.email is not None:
        existing_user = await get_user_by_email(
            db,
            user_data.email,
        )

        if (
            existing_user is not None
            and existing_user.id != user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

    if user_data.role_id is not None:
        role = await get_role_by_id(
            db,
            user_data.role_id,
        )

        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )

    return await update_user(
        db,
        user,
        user_data,
    )