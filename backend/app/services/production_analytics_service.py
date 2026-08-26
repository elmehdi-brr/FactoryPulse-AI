from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.production_run import ProductionRun
from app.production.analytics import (
    AggregatedOEEMetrics,
    ProductionAnalyticsError,
    RunOEEContribution,
    aggregate_oee,
)
from app.services.oee_service import (
    OEEServiceError,
    calculate_production_run_oee,
)


class ProductionAnalyticsServiceError(ValueError):
    pass


async def get_completed_runs_for_line(
    db: AsyncSession,
    production_line_id: int,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> list[ProductionRun]:
    query = select(ProductionRun).where(
        ProductionRun.production_line_id
        == production_line_id,
        ProductionRun.status == "completed",
        ProductionRun.ended_at.is_not(None),
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
        ProductionRun.started_at,
        ProductionRun.id,
    )

    result = await db.execute(query)

    return list(result.scalars().all())


async def calculate_production_line_oee(
    db: AsyncSession,
    production_line_id: int,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> AggregatedOEEMetrics:
    if (
        start_at is not None
        and end_at is not None
        and end_at <= start_at
    ):
        raise ProductionAnalyticsServiceError(
            "end_at must be later than start_at"
        )

    production_runs = await get_completed_runs_for_line(
        db,
        production_line_id,
        start_at=start_at,
        end_at=end_at,
    )

    if not production_runs:
        raise ProductionAnalyticsServiceError(
            "No completed production runs found for the selected period"
        )

    contributions: list[RunOEEContribution] = []

    for production_run in production_runs:
        if production_run.ideal_cycle_time_seconds is None:
            raise ProductionAnalyticsServiceError(
                "All production runs require ideal_cycle_time_seconds "
                "for aggregated OEE"
            )

        try:
            metrics = await calculate_production_run_oee(
                db,
                production_run,
            )
        except OEEServiceError as exc:
            raise ProductionAnalyticsServiceError(
                str(exc)
            ) from exc

        contributions.append(
            RunOEEContribution(
                metrics=metrics,
                ideal_cycle_time_seconds=(
                    production_run.ideal_cycle_time_seconds
                ),
                total_quantity=production_run.total_quantity,
                good_quantity=production_run.good_quantity,
            )
        )

    try:
        return aggregate_oee(
            contributions
        )
    except ProductionAnalyticsError as exc:
        raise ProductionAnalyticsServiceError(
            str(exc)
        ) from exc