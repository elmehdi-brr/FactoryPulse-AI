from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.downtime_event import DowntimeEvent
from app.models.machine import Machine
from app.models.production_run import ProductionRun
from app.schemas.downtime_event import (
    DowntimeEventCreate,
    DowntimeEventUpdate,
)
from app.services.machine_service import get_machine_by_id


class DowntimeEventValidationError(ValueError):
    pass


async def create_downtime_event(
    db: AsyncSession,
    downtime_data: DowntimeEventCreate,
) -> DowntimeEvent:
    downtime_event = DowntimeEvent(
        **downtime_data.model_dump()
    )

    db.add(downtime_event)
    await db.commit()
    await db.refresh(downtime_event)

    return downtime_event


async def get_downtime_event_by_id(
    db: AsyncSession,
    downtime_event_id: int,
) -> DowntimeEvent | None:
    result = await db.execute(
        select(DowntimeEvent).where(
            DowntimeEvent.id == downtime_event_id
        )
    )

    return result.scalar_one_or_none()


async def get_downtime_events(
    db: AsyncSession,
) -> list[DowntimeEvent]:
    result = await db.execute(
        select(DowntimeEvent).order_by(
            DowntimeEvent.started_at.desc(),
            DowntimeEvent.id.desc(),
        )
    )

    return list(result.scalars().all())


async def get_downtime_events_by_run(
    db: AsyncSession,
    production_run_id: int,
) -> list[DowntimeEvent]:
    result = await db.execute(
        select(DowntimeEvent)
        .where(
            DowntimeEvent.production_run_id
            == production_run_id
        )
        .order_by(
            DowntimeEvent.started_at.desc(),
            DowntimeEvent.id.desc(),
        )
    )

    return list(result.scalars().all())


async def validate_machine_for_production_run(
    db: AsyncSession,
    production_run: ProductionRun,
    machine_id: int | None,
) -> Machine | None:
    if machine_id is None:
        return None

    machine = await get_machine_by_id(
        db,
        machine_id,
    )

    if machine is None:
        raise DowntimeEventValidationError(
            "Machine not found"
        )

    if (
        machine.production_line_id
        != production_run.production_line_id
    ):
        raise DowntimeEventValidationError(
            "Machine does not belong to the production run's production line"
        )

    return machine


def validate_downtime_timing(
    production_run: ProductionRun,
    downtime_data: DowntimeEventCreate,
) -> None:
    if downtime_data.started_at < production_run.started_at:
        raise DowntimeEventValidationError(
            "Downtime event cannot start before the production run"
        )

    if production_run.ended_at is None:
        return

    if downtime_data.started_at > production_run.ended_at:
        raise DowntimeEventValidationError(
            "Downtime event cannot start after the production run ended"
        )

    if downtime_data.ended_at is None:
        raise DowntimeEventValidationError(
            "Downtime event requires ended_at when the production run has ended"
        )

    if downtime_data.ended_at > production_run.ended_at:
        raise DowntimeEventValidationError(
            "Downtime event cannot end after the production run ended"
        )


async def update_downtime_event(
    db: AsyncSession,
    downtime_event: DowntimeEvent,
    production_run: ProductionRun,
    downtime_data: DowntimeEventUpdate,
) -> DowntimeEvent:
    update_data = downtime_data.model_dump(
        exclude_unset=True
    )

    if not update_data:
        return downtime_event

    if downtime_event.ended_at is not None:
        raise DowntimeEventValidationError(
            "Closed downtime events cannot be modified"
        )

    final_data = {
        "production_run_id": downtime_event.production_run_id,
        "machine_id": downtime_event.machine_id,
        "category": downtime_event.category,
        "reason": downtime_event.reason,
        "started_at": downtime_event.started_at,
        "ended_at": downtime_event.ended_at,
        "notes": downtime_event.notes,
    }

    final_data.update(update_data)

    try:
        validated_state = DowntimeEventCreate.model_validate(
            final_data
        )
    except ValidationError as exc:
        raise DowntimeEventValidationError(
            str(exc)
        ) from exc

    validate_downtime_timing(
        production_run,
        validated_state,
    )

    validated_data = validated_state.model_dump()

    for field in update_data:
        setattr(
            downtime_event,
            field,
            validated_data[field],
        )

    await db.commit()
    await db.refresh(downtime_event)

    return downtime_event