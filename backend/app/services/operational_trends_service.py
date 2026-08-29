from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.production.operational_trends import (
    MachinePeriodSnapshot,
    OperationalPeriodSnapshot,
    OperationalTrendError,
    OperationalTrendSummary,
    calculate_operational_trends,
)
from app.services.operational_intelligence_service import (
    OperationalIntelligenceServiceError,
    ProductionLineOperationalIntelligenceResult,
    calculate_production_line_operational_intelligence,
)


class OperationalTrendsServiceError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class OperationalTrendPeriod:
    start_at: datetime
    end_at: datetime


@dataclass(frozen=True, slots=True)
class ProductionLineOperationalTrendsResult:
    production_line_id: int

    current_period: OperationalTrendPeriod
    previous_period: OperationalTrendPeriod

    current: ProductionLineOperationalIntelligenceResult
    previous: ProductionLineOperationalIntelligenceResult

    trends: OperationalTrendSummary


def validate_operational_trend_period(
    start_at: datetime,
    end_at: datetime,
) -> None:
    if end_at <= start_at:
        raise OperationalTrendsServiceError(
            "end_at must be later than start_at"
        )


def build_operational_period_snapshot(
    result: ProductionLineOperationalIntelligenceResult,
) -> OperationalPeriodSnapshot:
    machines = tuple(
        MachinePeriodSnapshot(
            machine_id=machine.machine_id,
            machine_name=machine.machine_name,
            machine_code=machine.machine_code,
            recorded_downtime_seconds=(
                machine.recorded_downtime_seconds
            ),
            failure_count=machine.failure_count,
            mttr_seconds=machine.mttr_seconds,
            mtbf_seconds=machine.mtbf_seconds,
        )
        for machine in result.operational_impact.machines
    )

    total_failure_count = sum(
        machine.failure_count
        for machine in result.operational_impact.machines
    )

    return OperationalPeriodSnapshot(
        oee=result.oee.oee,
        availability=result.oee.availability,
        performance=result.oee.performance,
        quality=result.oee.quality,
        recorded_downtime_seconds=(
            result.operational_impact.recorded_downtime_seconds
        ),
        total_failure_count=total_failure_count,
        machines=machines,
    )


async def calculate_production_line_operational_trends(
    db: AsyncSession,
    production_line_id: int,
    start_at: datetime,
    end_at: datetime,
) -> ProductionLineOperationalTrendsResult:
    validate_operational_trend_period(
        start_at,
        end_at,
    )

    period_duration = end_at - start_at

    previous_start_at = (
        start_at - period_duration
    )

    previous_end_at = start_at

    try:
        current = (
            await calculate_production_line_operational_intelligence(
                db,
                production_line_id,
                start_at=start_at,
                end_at=end_at,
            )
        )

        previous = (
            await calculate_production_line_operational_intelligence(
                db,
                production_line_id,
                start_at=previous_start_at,
                end_at=previous_end_at,
            )
        )

        current_snapshot = (
            build_operational_period_snapshot(
                current
            )
        )

        previous_snapshot = (
            build_operational_period_snapshot(
                previous
            )
        )

        trends = calculate_operational_trends(
            current_snapshot,
            previous_snapshot,
        )

    except (
        OperationalIntelligenceServiceError,
        OperationalTrendError,
    ) as exc:
        raise OperationalTrendsServiceError(
            str(exc)
        ) from exc

    return ProductionLineOperationalTrendsResult(
        production_line_id=production_line_id,
        current_period=OperationalTrendPeriod(
            start_at=start_at,
            end_at=end_at,
        ),
        previous_period=OperationalTrendPeriod(
            start_at=previous_start_at,
            end_at=previous_end_at,
        ),
        current=current,
        previous=previous,
        trends=trends,
    )