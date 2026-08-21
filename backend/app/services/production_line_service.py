from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.production_line import ProductionLine
from app.schemas.production_line import (
    ProductionLineCreate,
    ProductionLineUpdate,
)


async def create_production_line(
    db: AsyncSession,
    line_data: ProductionLineCreate,
) -> ProductionLine:
    production_line = ProductionLine(
        **line_data.model_dump()
    )

    db.add(production_line)
    await db.commit()
    await db.refresh(production_line)

    return production_line


async def get_production_line_by_id(
    db: AsyncSession,
    production_line_id: int,
) -> ProductionLine | None:
    result = await db.execute(
        select(ProductionLine).where(
            ProductionLine.id == production_line_id
        )
    )

    return result.scalar_one_or_none()


async def get_production_line_by_code(
    db: AsyncSession,
    code: str,
) -> ProductionLine | None:
    result = await db.execute(
        select(ProductionLine).where(
            ProductionLine.code == code.strip()
        )
    )

    return result.scalar_one_or_none()


async def get_production_lines(
    db: AsyncSession,
) -> list[ProductionLine]:
    result = await db.execute(
        select(ProductionLine).order_by(
            ProductionLine.id
        )
    )

    return list(result.scalars().all())


async def get_production_lines_by_area(
    db: AsyncSession,
    area_id: int,
) -> list[ProductionLine]:
    result = await db.execute(
        select(ProductionLine)
        .where(ProductionLine.area_id == area_id)
        .order_by(ProductionLine.id)
    )

    return list(result.scalars().all())


async def update_production_line(
    db: AsyncSession,
    production_line: ProductionLine,
    line_data: ProductionLineUpdate,
) -> ProductionLine:
    update_data = line_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(production_line, field, value)

    await db.commit()
    await db.refresh(production_line)

    return production_line