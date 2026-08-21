from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.area import Area
from app.schemas.area import AreaCreate, AreaUpdate


async def create_area(
    db: AsyncSession,
    area_data: AreaCreate,
) -> Area:
    area = Area(**area_data.model_dump())

    db.add(area)
    await db.commit()
    await db.refresh(area)

    return area


async def get_area_by_id(
    db: AsyncSession,
    area_id: int,
) -> Area | None:
    result = await db.execute(
        select(Area).where(Area.id == area_id)
    )

    return result.scalar_one_or_none()


async def get_area_by_code(
    db: AsyncSession,
    code: str,
) -> Area | None:
    result = await db.execute(
        select(Area).where(
            Area.code == code.strip()
        )
    )

    return result.scalar_one_or_none()


async def get_areas(
    db: AsyncSession,
) -> list[Area]:
    result = await db.execute(
        select(Area).order_by(Area.id)
    )

    return list(result.scalars().all())


async def get_areas_by_site(
    db: AsyncSession,
    site_id: int,
) -> list[Area]:
    result = await db.execute(
        select(Area)
        .where(Area.site_id == site_id)
        .order_by(Area.id)
    )

    return list(result.scalars().all())


async def update_area(
    db: AsyncSession,
    area: Area,
    area_data: AreaUpdate,
) -> Area:
    update_data = area_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(area, field, value)

    await db.commit()
    await db.refresh(area)

    return area