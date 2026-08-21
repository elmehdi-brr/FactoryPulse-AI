from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationUpdate


async def create_organization(
    db: AsyncSession,
    organization_data: OrganizationCreate,
) -> Organization:
    organization = Organization(**organization_data.model_dump())

    db.add(organization)
    await db.commit()
    await db.refresh(organization)

    return organization


async def get_organization_by_id(
    db: AsyncSession,
    organization_id: int,
) -> Organization | None:
    result = await db.execute(
        select(Organization).where(
            Organization.id == organization_id
        )
    )

    return result.scalar_one_or_none()


async def get_organization_by_code(
    db: AsyncSession,
    code: str,
) -> Organization | None:
    result = await db.execute(
        select(Organization).where(
            Organization.code == code.strip()
        )
    )

    return result.scalar_one_or_none()


async def get_organizations(
    db: AsyncSession,
) -> list[Organization]:
    result = await db.execute(
        select(Organization).order_by(Organization.id)
    )

    return list(result.scalars().all())


async def update_organization(
    db: AsyncSession,
    organization: Organization,
    organization_data: OrganizationUpdate,
) -> Organization:
    update_data = organization_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(organization, field, value)

    await db.commit()
    await db.refresh(organization)

    return organization