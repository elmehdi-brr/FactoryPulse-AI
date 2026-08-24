from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.models.role import Role


async def get_user_by_id(
    db: AsyncSession,
    user_id: int,
) -> User | None:
    result = await db.execute(
        select(User).where(User.id == user_id)
    )

    return result.scalar_one_or_none()


async def get_user_by_email(
    db: AsyncSession,
    email: str,
) -> User | None:
    normalized_email = email.strip().lower()

    result = await db.execute(
        select(User).where(User.email == normalized_email)
    )

    return result.scalar_one_or_none()


async def get_users(
    db: AsyncSession,
) -> list[User]:
    result = await db.execute(
        select(User).order_by(User.id)
    )

    return list(result.scalars().all())

async def get_active_users_by_roles(
    db: AsyncSession,
    role_names: Sequence[str],
) -> list[User]:
    result = await db.execute(
        select(User)
        .join(
            Role,
            User.role_id == Role.id,
        )
        .where(
            User.is_active.is_(True),
            Role.name.in_(role_names),
        )
        .order_by(User.id)
    )

    return list(result.scalars().all())


async def create_user(
    db: AsyncSession,
    user_data: UserCreate,
) -> User:
    user = User(
        email=user_data.email.strip().lower(),
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
        role_id=user_data.role_id,
        is_active=True,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


async def update_user(
    db: AsyncSession,
    user: User,
    user_data: UserUpdate,
) -> User:
    update_data = user_data.model_dump(exclude_unset=True)

    password = update_data.pop("password", None)

    if password is not None:
        user.hashed_password = hash_password(password)

    if "email" in update_data and update_data["email"] is not None:
        update_data["email"] = update_data["email"].strip().lower()

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return user