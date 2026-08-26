from sqlalchemy.ext.asyncio import AsyncSession

from app.models.production_run import ProductionRun
from app.production.oee import (
    DowntimeWindow,
    OEECalculationError,
    OEEMetrics,
    calculate_oee,
)
from app.services.downtime_event_service import (
    get_downtime_events_by_run,
)


class OEEServiceError(ValueError):
    pass


async def calculate_production_run_oee(
    db: AsyncSession,
    production_run: ProductionRun,
) -> OEEMetrics:
    if production_run.status != "completed":
        raise OEEServiceError(
            "OEE can only be calculated for completed production runs"
        )

    if production_run.ended_at is None:
        raise OEEServiceError(
            "Completed production run requires ended_at"
        )

    downtime_events = await get_downtime_events_by_run(
        db,
        production_run.id,
    )

    downtime_windows = [
        DowntimeWindow(
            started_at=downtime_event.started_at,
            ended_at=downtime_event.ended_at,
            category=downtime_event.category,
        )
        for downtime_event in downtime_events
    ]

    try:
        return calculate_oee(
            started_at=production_run.started_at,
            ended_at=production_run.ended_at,
            ideal_cycle_time_seconds=(
                production_run.ideal_cycle_time_seconds
            ),
            total_quantity=production_run.total_quantity,
            good_quantity=production_run.good_quantity,
            downtime_windows=downtime_windows,
        )
    except OEECalculationError as exc:
        raise OEEServiceError(
            str(exc)
        ) from exc