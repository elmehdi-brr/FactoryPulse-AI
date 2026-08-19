from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role


async def get_role_by_id(
    db: AsyncSession,
    role_id: int,
) -> Role | None:
    result = await db.execute(
        select(Role).where(Role.id == role_id)
    )

    return result.scalar_one_or_none()


async def get_role_by_name(
    db: AsyncSession,
    name: str,
) -> Role | None:
    result = await db.execute(
        select(Role).where(Role.name == name)
    )

    return result.scalar_one_or_none()


async def get_roles(
    db: AsyncSession,
) -> list[Role]:
    result = await db.execute(
        select(Role).order_by(Role.id)
    )

    return list(result.scalars().all())