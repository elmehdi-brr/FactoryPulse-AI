from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.models.user import User
from app.services.user_service import get_user_by_email


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> User | None:
    user = await get_user_by_email(db, email)

    if user is None:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    if not user.is_active:
        return None

    return user