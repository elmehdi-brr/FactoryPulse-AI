from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.downtime_event import DowntimeEvent
from app.production.reliability import (
    MachineFailureEvent,
    MachineFailureMetrics,
    MachineReliabilityError,
    calculate_machine_failure_metrics,
)


class MachineReliabilityServiceError(ValueError):
    pass


async def get_machine_failure_events(
    db: AsyncSession,
    machine_id: int,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> list[DowntimeEvent]:
    if (
        start_at is not None
        and end_at is not None
        and end_at <= start_at
    ):
        raise MachineReliabilityServiceError(
            "end_at must be later than start_at"
        )

    query = select(DowntimeEvent).where(
        DowntimeEvent.machine_id == machine_id,
        DowntimeEvent.category == "unplanned",
        DowntimeEvent.ended_at.is_not(None),
    )

    if start_at is not None:
        query = query.where(
            DowntimeEvent.started_at >= start_at
        )

    if end_at is not None:
        query = query.where(
            DowntimeEvent.ended_at <= end_at
        )

    query = query.order_by(
        DowntimeEvent.started_at,
        DowntimeEvent.id,
    )

    result = await db.execute(query)

    return list(result.scalars().all())


async def calculate_machine_reliability(
    db: AsyncSession,
    machine_id: int,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> MachineFailureMetrics:
    downtime_events = await get_machine_failure_events(
        db,
        machine_id,
        start_at=start_at,
        end_at=end_at,
    )

    failures = [
        MachineFailureEvent(
            started_at=event.started_at,
            ended_at=event.ended_at,
        )
        for event in downtime_events
    ]

    try:
        return calculate_machine_failure_metrics(
            failures
        )
    except MachineReliabilityError as exc:
        raise MachineReliabilityServiceError(
            str(exc)
        ) from exc