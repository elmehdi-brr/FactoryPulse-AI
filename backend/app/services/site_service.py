from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.site import Site
from app.schemas.site import SiteCreate, SiteUpdate


async def create_site(
    db: AsyncSession,
    site_data: SiteCreate,
) -> Site:
    site = Site(**site_data.model_dump())

    db.add(site)
    await db.commit()
    await db.refresh(site)

    return site


async def get_site_by_id(
    db: AsyncSession,
    site_id: int,
) -> Site | None:
    result = await db.execute(
        select(Site).where(Site.id == site_id)
    )

    return result.scalar_one_or_none()


async def get_site_by_code(
    db: AsyncSession,
    code: str,
) -> Site | None:
    result = await db.execute(
        select(Site).where(
            Site.code == code.strip()
        )
    )

    return result.scalar_one_or_none()


async def get_sites(
    db: AsyncSession,
) -> list[Site]:
    result = await db.execute(
        select(Site).order_by(Site.id)
    )

    return list(result.scalars().all())


async def get_sites_by_organization(
    db: AsyncSession,
    organization_id: int,
) -> list[Site]:
    result = await db.execute(
        select(Site)
        .where(Site.organization_id == organization_id)
        .order_by(Site.id)
    )

    return list(result.scalars().all())


async def update_site(
    db: AsyncSession,
    site: Site,
    site_data: SiteUpdate,
) -> Site:
    update_data = site_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(site, field, value)

    await db.commit()
    await db.refresh(site)

    return site