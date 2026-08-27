from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.downtime_event import DowntimeEvent
from app.models.machine import Machine
from app.models.production_run import ProductionRun
from app.production.reliability import (
    MachineFailureEvent,
    MachineReliabilityError,
    MachineReliabilityMetrics,
    ReliabilityDowntimeWindow,
    calculate_machine_reliability_metrics,
    calculate_operating_exposure_seconds,
)
from app.services.production_analytics_service import (
    get_completed_runs_for_line,
)


class MachineReliabilityServiceError(ValueError):
    pass


def validate_reliability_period(
    start_at: datetime | None,
    end_at: datetime | None,
) -> None:
    if (
        start_at is not None
        and end_at is not None
        and end_at <= start_at
    ):
        raise MachineReliabilityServiceError(
            "end_at must be later than start_at"
        )


async def get_machine_failure_events(
    db: AsyncSession,
    machine_id: int,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> list[DowntimeEvent]:
    validate_reliability_period(
        start_at,
        end_at,
    )

    query = (
        select(DowntimeEvent)
        .join(
            ProductionRun,
            DowntimeEvent.production_run_id
            == ProductionRun.id,
        )
        .where(
            DowntimeEvent.machine_id == machine_id,
            DowntimeEvent.category == "unplanned",
            DowntimeEvent.ended_at.is_not(None),
            ProductionRun.status == "completed",
            ProductionRun.ended_at.is_not(None),
        )
    )

    if start_at is not None:
        query = query.where(
            ProductionRun.started_at >= start_at
        )

    if end_at is not None:
        query = query.where(
            ProductionRun.ended_at <= end_at
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
) -> MachineReliabilityMetrics:
    validate_reliability_period(
        start_at,
        end_at,
    )

    machine_result = await db.execute(
        select(Machine).where(
            Machine.id == machine_id
        )
    )

    machine = machine_result.scalar_one_or_none()

    if machine is None:
        raise MachineReliabilityServiceError(
            "Machine not found"
        )

    failure_events = await get_machine_failure_events(
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
        for event in failure_events
    ]

    # Standalone machines do not yet have a trustworthy
    # production-runtime exposure source.
    if machine.production_line_id is None:
        try:
            return calculate_machine_reliability_metrics(
                failures,
                operating_exposure_seconds=None,
            )
        except MachineReliabilityError as exc:
            raise MachineReliabilityServiceError(
                str(exc)
            ) from exc

    production_runs = await get_completed_runs_for_line(
        db,
        machine.production_line_id,
        start_at=start_at,
        end_at=end_at,
    )

    if not production_runs:
        try:
            return calculate_machine_reliability_metrics(
                failures,
                operating_exposure_seconds=0.0,
            )
        except MachineReliabilityError as exc:
            raise MachineReliabilityServiceError(
                str(exc)
            ) from exc

    production_run_ids = [
        production_run.id
        for production_run in production_runs
    ]

    downtime_result = await db.execute(
        select(DowntimeEvent)
        .where(
            DowntimeEvent.production_run_id.in_(
                production_run_ids
            )
        )
        .order_by(
            DowntimeEvent.production_run_id,
            DowntimeEvent.started_at,
            DowntimeEvent.id,
        )
    )

    downtime_events = list(
        downtime_result.scalars().all()
    )

    downtime_by_run: dict[
        int,
        list[DowntimeEvent],
    ] = {
        production_run_id: []
        for production_run_id in production_run_ids
    }

    for downtime_event in downtime_events:
        downtime_by_run[
            downtime_event.production_run_id
        ].append(
            downtime_event
        )

    operating_exposure_seconds = 0.0

    try:
        for production_run in production_runs:
            if production_run.ended_at is None:
                raise MachineReliabilityError(
                    "Completed production run requires ended_at"
                )

            downtime_windows = [
                ReliabilityDowntimeWindow(
                    started_at=event.started_at,
                    ended_at=event.ended_at,
                )
                for event in downtime_by_run[
                    production_run.id
                ]
            ]

            operating_exposure_seconds += (
                calculate_operating_exposure_seconds(
                    started_at=production_run.started_at,
                    ended_at=production_run.ended_at,
                    downtime_windows=downtime_windows,
                )
            )

        return calculate_machine_reliability_metrics(
            failures,
            operating_exposure_seconds=(
                operating_exposure_seconds
            ),
        )

    except MachineReliabilityError as exc:
        raise MachineReliabilityServiceError(
            str(exc)
        ) from exc