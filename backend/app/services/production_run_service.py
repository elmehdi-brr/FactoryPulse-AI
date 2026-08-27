from pydantic import ValidationError
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app.models.production_run import ProductionRun
from app.models.downtime_event import DowntimeEvent
from app.schemas.production_run import (
    ProductionRunCreate,
    ProductionRunUpdate,
)


class ProductionRunValidationError(ValueError):
    pass

PRODUCTION_RUN_OVERLAP_CONSTRAINT = (
    "ex_production_runs_line_time_overlap"
)

async def create_production_run(
    db: AsyncSession,
    run_data: ProductionRunCreate,
) -> ProductionRun:
    await validate_production_run_overlap(
        db,
        production_line_id=run_data.production_line_id,
        started_at=run_data.started_at,
        ended_at=run_data.ended_at,
    )

    production_run = ProductionRun(
        **run_data.model_dump()
    )

    db.add(production_run)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()

        if (
            PRODUCTION_RUN_OVERLAP_CONSTRAINT
            in str(exc.orig)
        ):
            raise ProductionRunValidationError(
                "Production run overlaps an existing run "
                "on the same production line"
            ) from exc

        raise

    await db.refresh(production_run)

    return production_run


async def get_production_run_by_id(
    db: AsyncSession,
    production_run_id: int,
) -> ProductionRun | None:
    result = await db.execute(
        select(ProductionRun).where(
            ProductionRun.id == production_run_id
        )
    )

    return result.scalar_one_or_none()


async def get_production_runs(
    db: AsyncSession,
) -> list[ProductionRun]:
    result = await db.execute(
        select(ProductionRun).order_by(
            ProductionRun.started_at.desc(),
            ProductionRun.id.desc(),
        )
    )

    return list(result.scalars().all())


async def get_production_runs_by_line(
    db: AsyncSession,
    production_line_id: int,
) -> list[ProductionRun]:
    result = await db.execute(
        select(ProductionRun)
        .where(
            ProductionRun.production_line_id
            == production_line_id
        )
        .order_by(
            ProductionRun.started_at.desc(),
            ProductionRun.id.desc(),
        )
    )

    return list(result.scalars().all())

async def validate_downtime_for_production_run_end(
    db: AsyncSession,
    production_run_id: int,
    ended_at: datetime,
) -> None:
    result = await db.execute(
        select(DowntimeEvent).where(
            DowntimeEvent.production_run_id
            == production_run_id
        )
    )

    downtime_events = list(
        result.scalars().all()
    )

    for downtime_event in downtime_events:
        if downtime_event.ended_at is None:
            raise ProductionRunValidationError(
                "Production run cannot end while downtime events are still open"
            )

        if downtime_event.started_at > ended_at:
            raise ProductionRunValidationError(
                "Production run cannot end before its downtime events"
            )

        if downtime_event.ended_at > ended_at:
            raise ProductionRunValidationError(
                "Production run cannot end before its downtime events"
            )


async def validate_production_run_overlap(
    db: AsyncSession,
    production_line_id: int,
    started_at: datetime,
    ended_at: datetime | None,
    *,
    exclude_production_run_id: int | None = None,
) -> None:
    query = select(ProductionRun).where(
        ProductionRun.production_line_id
        == production_line_id,
    )

    if exclude_production_run_id is not None:
        query = query.where(
            ProductionRun.id
            != exclude_production_run_id
        )

    if ended_at is None:
        query = query.where(
            or_(
                ProductionRun.ended_at.is_(None),
                ProductionRun.ended_at > started_at,
            )
        )
    else:
        query = query.where(
            ProductionRun.started_at < ended_at,
            or_(
                ProductionRun.ended_at.is_(None),
                ProductionRun.ended_at > started_at,
            ),
        )

    result = await db.execute(query)

    overlapping_run = result.scalars().first()

    if overlapping_run is not None:
        raise ProductionRunValidationError(
            "Production run overlaps an existing run "
            "on the same production line"
        )


async def update_production_run(
    db: AsyncSession,
    production_run: ProductionRun,
    run_data: ProductionRunUpdate,
) -> ProductionRun:
    update_data = run_data.model_dump(
        exclude_unset=True
    )

    if not update_data:
        return production_run

    if production_run.status in {
        "completed",
        "cancelled",
    }:
        raise ProductionRunValidationError(
            "Completed or cancelled production runs cannot be modified"
        )

    final_data = {
        "production_line_id": production_run.production_line_id,
        "started_at": production_run.started_at,
        "ended_at": production_run.ended_at,
        "status": production_run.status,
        "target_quantity": production_run.target_quantity,
        "total_quantity": production_run.total_quantity,
        "good_quantity": production_run.good_quantity,
        "reject_quantity": production_run.reject_quantity,
        "ideal_cycle_time_seconds": (
            production_run.ideal_cycle_time_seconds
        ),
    }

    final_data.update(update_data)

    try:
        validated_state = ProductionRunCreate.model_validate(
            final_data
        )
    except ValidationError as exc:
        raise ProductionRunValidationError(
            str(exc)
        ) from exc

    if validated_state.status in {
        "completed",
        "cancelled",
    }:
        if validated_state.ended_at is None:
            raise ProductionRunValidationError(
                "Ended production runs require ended_at"
            )

        await validate_downtime_for_production_run_end(
            db,
            production_run.id,
            validated_state.ended_at,
        )

    validated_data = validated_state.model_dump()

    for field in update_data:
        setattr(
            production_run,
            field,
            validated_data[field],
        )

    await db.commit()
    await db.refresh(production_run)

    return production_run