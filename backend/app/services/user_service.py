from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate


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