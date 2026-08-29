from dataclasses import dataclass
from datetime import datetime
from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.downtime_event import DowntimeEvent
from app.production.downtime_analytics import (
    DowntimeAnalyticsError,
    DowntimeAnalyticsEvent,
    DowntimeAnalyticsMetrics,
    DowntimeCategory,
    calculate_downtime_analytics,
)
from app.services.production_analytics_service import (
    get_completed_runs_for_line,
)


class DowntimeAnalyticsServiceError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ProductionLineDowntimeAnalyticsResult:
    run_count: int
    metrics: DowntimeAnalyticsMetrics
    events: tuple[DowntimeAnalyticsEvent, ...]


async def calculate_production_line_downtime_analytics(
    db: AsyncSession,
    production_line_id: int,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> ProductionLineDowntimeAnalyticsResult:
    if (
        start_at is not None
        and end_at is not None
        and end_at <= start_at
    ):
        raise DowntimeAnalyticsServiceError(
            "end_at must be later than start_at"
        )

    production_runs = await get_completed_runs_for_line(
        db,
        production_line_id,
        start_at=start_at,
        end_at=end_at,
    )

    if not production_runs:
        raise DowntimeAnalyticsServiceError(
            "No completed production runs found for the selected period"
        )

    production_run_ids = [
        production_run.id
        for production_run in production_runs
    ]

    query = (
        select(DowntimeEvent)
        .where(
            DowntimeEvent.production_run_id.in_(
                production_run_ids
            )
        )
        .order_by(
            DowntimeEvent.started_at,
            DowntimeEvent.id,
        )
    )

    result = await db.execute(query)

    downtime_events = list(
        result.scalars().all()
    )

    analytics_events = [
        DowntimeAnalyticsEvent(
            reason=downtime_event.reason,
            category=cast(
                DowntimeCategory,
                downtime_event.category,
            ),
            started_at=downtime_event.started_at,
            ended_at=downtime_event.ended_at,
            machine_id=downtime_event.machine_id,
        )
        for downtime_event in downtime_events
    ]

    try:
        metrics = calculate_downtime_analytics(
            analytics_events
        )
    except DowntimeAnalyticsError as exc:
        raise DowntimeAnalyticsServiceError(
            str(exc)
        ) from exc

    return ProductionLineDowntimeAnalyticsResult(
        run_count=len(production_runs),
        metrics=metrics,
        events=tuple(analytics_events),
    )