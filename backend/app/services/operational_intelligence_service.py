from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.machine import Machine
from app.production.analytics import AggregatedOEEMetrics
from app.production.downtime_analytics import (
    DowntimeAnalyticsMetrics,
)
from app.production.operational_intelligence import (
    MachineReliabilitySnapshot,
    OperationalDowntimeSummary,
    OperationalIntelligenceError,
    calculate_operational_downtime_impact,
    OperationalPrioritySummary,
    calculate_operational_priority,
)
from app.services.downtime_analytics_service import (
    DowntimeAnalyticsServiceError,
    calculate_production_line_downtime_analytics,
)
from app.services.machine_reliability_service import (
    MachineReliabilityServiceError,
    calculate_machine_reliability,
)
from app.services.production_analytics_service import (
    ProductionAnalyticsServiceError,
    calculate_production_line_oee,
)


class OperationalIntelligenceServiceError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ProductionLineOperationalIntelligenceResult:
    production_line_id: int

    start_at: datetime | None
    end_at: datetime | None

    run_count: int

    oee: AggregatedOEEMetrics
    downtime: DowntimeAnalyticsMetrics
    operational_impact: OperationalDowntimeSummary
    priority: OperationalPrioritySummary


def validate_operational_intelligence_period(
    start_at: datetime | None,
    end_at: datetime | None,
) -> None:
    if (
        start_at is not None
        and end_at is not None
        and end_at <= start_at
    ):
        raise OperationalIntelligenceServiceError(
            "end_at must be later than start_at"
        )


async def get_production_line_machines(
    db: AsyncSession,
    production_line_id: int,
) -> list[Machine]:
    result = await db.execute(
        select(Machine)
        .where(
            Machine.production_line_id
            == production_line_id
        )
        .order_by(
            Machine.code,
            Machine.id,
        )
    )

    return list(result.scalars().all())


async def calculate_production_line_operational_intelligence(
    db: AsyncSession,
    production_line_id: int,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> ProductionLineOperationalIntelligenceResult:
    validate_operational_intelligence_period(
        start_at,
        end_at,
    )

    try:
        oee_metrics = await calculate_production_line_oee(
            db,
            production_line_id,
            start_at=start_at,
            end_at=end_at,
        )

        downtime_result = (
            await calculate_production_line_downtime_analytics(
                db,
                production_line_id,
                start_at=start_at,
                end_at=end_at,
            )
        )

        machines = await get_production_line_machines(
            db,
            production_line_id,
        )

        machine_snapshots: list[
            MachineReliabilitySnapshot
        ] = []

        for machine in machines:
            reliability = await calculate_machine_reliability(
                db,
                machine.id,
                start_at=start_at,
                end_at=end_at,
            )

            machine_snapshots.append(
                MachineReliabilitySnapshot(
                    machine_id=machine.id,
                    machine_name=machine.name,
                    machine_code=machine.code,
                    failure_count=(
                        reliability.failure_count
                    ),
                    mttr_seconds=(
                        reliability.mttr_seconds
                    ),
                    operating_exposure_seconds=(
                        reliability.operating_exposure_seconds
                    ),
                    mtbf_seconds=(
                        reliability.mtbf_seconds
                    ),
                )
            )

        operational_impact = (
            calculate_operational_downtime_impact(
                downtime_result.metrics,
                machine_snapshots,
            )
        )
        priority = calculate_operational_priority(
            operational_impact.machines
        )

    except (
        ProductionAnalyticsServiceError,
        DowntimeAnalyticsServiceError,
        MachineReliabilityServiceError,
        OperationalIntelligenceError,
    ) as exc:
        raise OperationalIntelligenceServiceError(
            str(exc)
        ) from exc

    return ProductionLineOperationalIntelligenceResult(
        production_line_id=production_line_id,
        start_at=start_at,
        end_at=end_at,
        run_count=downtime_result.run_count,
        oee=oee_metrics,
        downtime=downtime_result.metrics,
        operational_impact=operational_impact,
        priority=priority,
    )