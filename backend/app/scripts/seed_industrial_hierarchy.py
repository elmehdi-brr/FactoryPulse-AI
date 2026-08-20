import asyncio

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.area import Area
from app.models.machine import Machine
from app.models.organization import Organization
from app.models.production_line import ProductionLine
from app.models.site import Site


async def seed_industrial_hierarchy() -> None:
    async with AsyncSessionLocal() as db:
        # Organization
        result = await db.execute(
            select(Organization).where(
                Organization.code == "FP-DEMO"
            )
        )
        organization = result.scalar_one_or_none()

        if organization is None:
            organization = Organization(
                name="FactoryPulse Demo Industries",
                code="FP-DEMO",
                description="Demo industrial organization for FactoryPulse AI.",
            )
            db.add(organization)
            await db.flush()

        # Site
        result = await db.execute(
            select(Site).where(
                Site.code == "TNG-FACTORY"
            )
        )
        site = result.scalar_one_or_none()

        if site is None:
            site = Site(
                organization_id=organization.id,
                name="Tangier Factory",
                code="TNG-FACTORY",
                location="Tangier, Morocco",
                description="Primary FactoryPulse demonstration industrial site.",
            )
            db.add(site)
            await db.flush()

        # Area
        result = await db.execute(
            select(Area).where(
                Area.code == "PROD-AREA-01"
            )
        )
        area = result.scalar_one_or_none()

        if area is None:
            area = Area(
                site_id=site.id,
                name="Production Area",
                code="PROD-AREA-01",
                description="Main production area.",
            )
            db.add(area)
            await db.flush()

        # Production Line
        result = await db.execute(
            select(ProductionLine).where(
                ProductionLine.code == "LINE-01"
            )
        )
        production_line = result.scalar_one_or_none()

        if production_line is None:
            production_line = ProductionLine(
                area_id=area.id,
                name="Production Line 1",
                code="LINE-01",
                description="Primary demonstration production line.",
            )
            db.add(production_line)
            await db.flush()

        # Existing development machine
        result = await db.execute(
            select(Machine).where(
                Machine.code == "MOTOR-001"
            )
        )
        machine = result.scalar_one_or_none()

        if machine is not None:
            machine.area_id = area.id
            machine.production_line_id = production_line.id

        await db.commit()

        print("Industrial hierarchy seeded successfully.")

        if machine is not None:
            print(
                f"{machine.code} -> "
                f"{organization.code} / "
                f"{site.code} / "
                f"{area.code} / "
                f"{production_line.code}"
            )


if __name__ == "__main__":
    asyncio.run(seed_industrial_hierarchy())