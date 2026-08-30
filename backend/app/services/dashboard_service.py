from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.machine import Machine
from app.models.production_run import ProductionRun
from app.models.sensor import Sensor
from app.production.analytics import (
    AggregatedOEEMetrics,
)
from app.production.operational_intelligence import (
    MachineOperationalImpact,
    OperationalIntelligenceError,
    calculate_operational_priority,
)
from app.services.machine_reliability_service import (
    MachineReliabilityServiceError,
    calculate_machine_reliability,
)
from app.services.machine_service import get_machines
from app.services.production_analytics_service import (
    ProductionAnalyticsServiceError,
    calculate_aggregated_oee_for_runs,
    get_completed_runs_for_line,
)
from app.services.production_line_service import (
    get_production_lines,
)
from app.services.operational_intelligence_service import (
    OperationalIntelligenceServiceError,
    calculate_production_line_operational_intelligence,
)


class DashboardServiceError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class DashboardProductionLineMetrics:
    id: int
    name: str
    code: str

    oee: float | None
    availability: float | None


@dataclass(frozen=True, slots=True)
class DashboardMachineHealthMetrics:
    total_machines: int

    healthy_count: int
    attention_count: int
    critical_count: int


@dataclass(frozen=True, slots=True)
class DashboardRecentAlertMetrics:
    id: int

    machine_id: int
    machine_name: str
    machine_code: str

    severity: str
    title: str
    message: str

    created_at: datetime

@dataclass(frozen=True, slots=True)
class DashboardNeedsAttentionMetrics:
    machine_id: int
    machine_name: str
    machine_code: str

    production_line_id: int
    production_line_name: str

    priority_rank: int

    recorded_downtime_seconds: float
    failure_count: int

    mttr_seconds: float | None
    mtbf_seconds: float | None

    dominant_reason: str | None
    dominant_reason_percentage: float | None

@dataclass(frozen=True, slots=True)
class DashboardOverviewMetrics:
    start_at: datetime | None
    end_at: datetime | None

    overall_oee: float | None
    availability: float | None

    needs_attention: DashboardNeedsAttentionMetrics | None

    active_alert_count: int

    fleet_mtbf_seconds: float | None

    production_lines: list[
        DashboardProductionLineMetrics
    ]

    machine_health: DashboardMachineHealthMetrics

    recent_alerts: list[
        DashboardRecentAlertMetrics
    ]


def validate_dashboard_period(
    start_at: datetime | None,
    end_at: datetime | None,
) -> None:
    if (
        start_at is not None
        and end_at is not None
        and end_at <= start_at
    ):
        raise DashboardServiceError(
            "end_at must be later than start_at"
        )


async def get_active_alert_count(
    db: AsyncSession,
) -> int:
    result = await db.execute(
        select(
            func.count(Alert.id)
        ).where(
            Alert.status == "open"
        )
    )

    return int(result.scalar_one())


async def calculate_machine_health(
    db: AsyncSession,
) -> DashboardMachineHealthMetrics:
    machines = await get_machines(db)

    machine_health: dict[int, str] = {
        machine.id: "healthy"
        for machine in machines
    }

    result = await db.execute(
        select(
            Sensor.machine_id,
            Alert.severity,
        )
        .join(
            Alert,
            Alert.sensor_id == Sensor.id,
        )
        .where(
            Alert.status == "open"
        )
    )

    for machine_id, severity in result.all():
        current_health = machine_health.get(
            machine_id
        )

        if current_health is None:
            continue

        normalized_severity = (
            severity.strip().lower()
        )

        if normalized_severity == "critical":
            machine_health[machine_id] = (
                "critical"
            )

            continue

        if current_health != "critical":
            machine_health[machine_id] = (
                "attention"
            )

    healthy_count = sum(
        health == "healthy"
        for health in machine_health.values()
    )

    attention_count = sum(
        health == "attention"
        for health in machine_health.values()
    )

    critical_count = sum(
        health == "critical"
        for health in machine_health.values()
    )

    return DashboardMachineHealthMetrics(
        total_machines=len(machines),
        healthy_count=healthy_count,
        attention_count=attention_count,
        critical_count=critical_count,
    )


async def get_recent_open_alerts(
    db: AsyncSession,
    limit: int = 3,
) -> list[DashboardRecentAlertMetrics]:
    result = await db.execute(
        select(
            Alert,
            Machine,
        )
        .join(
            Sensor,
            Alert.sensor_id == Sensor.id,
        )
        .join(
            Machine,
            Sensor.machine_id == Machine.id,
        )
        .where(
            Alert.status == "open"
        )
        .order_by(
            Alert.created_at.desc(),
            Alert.id.desc(),
        )
        .limit(limit)
    )

    return [
        DashboardRecentAlertMetrics(
            id=alert.id,
            machine_id=machine.id,
            machine_name=machine.name,
            machine_code=machine.code,
            severity=alert.severity,
            title=alert.title,
            message=alert.message,
            created_at=alert.created_at,
        )
        for alert, machine in result.all()
    ]


async def calculate_fleet_mtbf(
    db: AsyncSession,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> float | None:
    machines = await get_machines(db)

    total_operating_exposure_seconds = 0.0
    total_failure_count = 0

    has_valid_exposure = False

    for machine in machines:
        try:
            reliability = (
                await calculate_machine_reliability(
                    db,
                    machine.id,
                    start_at=start_at,
                    end_at=end_at,
                )
            )
        except MachineReliabilityServiceError as exc:
            raise DashboardServiceError(
                str(exc)
            ) from exc

        if (
            reliability.operating_exposure_seconds
            is None
        ):
            continue

        has_valid_exposure = True

        total_operating_exposure_seconds += (
            reliability.operating_exposure_seconds
        )

        total_failure_count += (
            reliability.failure_count
        )

    if not has_valid_exposure:
        return None

    if total_failure_count == 0:
        return None

    return (
        total_operating_exposure_seconds
        / total_failure_count
    )


async def calculate_factory_needs_attention(
    db: AsyncSession,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> DashboardNeedsAttentionMetrics | None:
    production_lines = await get_production_lines(
        db
    )

    all_machine_impacts: list[
        MachineOperationalImpact
    ] = []

    line_by_machine_id: dict[
        int,
        tuple[int, str],
    ] = {}

    reason_by_machine_id: dict[
        int,
        tuple[str | None, float | None],
    ] = {}

    for production_line in production_lines:
        completed_runs = (
            await get_completed_runs_for_line(
                db,
                production_line.id,
                start_at=start_at,
                end_at=end_at,
            )
        )

        if not completed_runs:
            continue

        try:
            intelligence = (
                await calculate_production_line_operational_intelligence(
                    db,
                    production_line.id,
                    start_at=start_at,
                    end_at=end_at,
                )
            )
        except OperationalIntelligenceServiceError as exc:
            raise DashboardServiceError(
                str(exc)
            ) from exc

        for machine in (
            intelligence.operational_impact.machines
        ):
            all_machine_impacts.append(
                machine
            )

            line_by_machine_id[
                machine.machine_id
            ] = (
                production_line.id,
                production_line.name,
            )

        for reason_summary in (
            intelligence.downtime_reasons
        ):
            dominant_reason = (
                reason_summary.dominant_duration_reason
            )

            dominant_percentage: (
                float | None
            ) = None

            if dominant_reason is not None:
                for reason in reason_summary.by_reason:
                    if (
                        reason.reason
                        == dominant_reason
                    ):
                        dominant_percentage = (
                            reason.percentage
                        )
                        break

            reason_by_machine_id[
                reason_summary.machine_id
            ] = (
                dominant_reason,
                dominant_percentage,
            )

    if not all_machine_impacts:
        return None

    try:
        priority = calculate_operational_priority(
            all_machine_impacts
        )
    except OperationalIntelligenceError as exc:
        raise DashboardServiceError(
            str(exc)
        ) from exc

    top_machine_id = (
        priority.top_priority_machine_id
    )

    if top_machine_id is None:
        return None

    impact_by_machine_id = {
        machine.machine_id: machine
        for machine in all_machine_impacts
    }

    priority_by_machine_id = {
        machine.machine_id: machine
        for machine in priority.machines
    }

    top_impact = impact_by_machine_id[
        top_machine_id
    ]

    top_priority = priority_by_machine_id[
        top_machine_id
    ]

    production_line_id, production_line_name = (
        line_by_machine_id[
            top_machine_id
        ]
    )

    dominant_reason, dominant_percentage = (
        reason_by_machine_id.get(
            top_machine_id,
            (None, None),
        )
    )

    if top_priority.priority_rank is None:
        return None

    return DashboardNeedsAttentionMetrics(
        machine_id=top_impact.machine_id,
        machine_name=top_impact.machine_name,
        machine_code=top_impact.machine_code,
        production_line_id=production_line_id,
        production_line_name=production_line_name,
        priority_rank=(
            top_priority.priority_rank
        ),
        recorded_downtime_seconds=(
            top_impact.recorded_downtime_seconds
        ),
        failure_count=(
            top_impact.failure_count
        ),
        mttr_seconds=(
            top_impact.mttr_seconds
        ),
        mtbf_seconds=(
            top_impact.mtbf_seconds
        ),
        dominant_reason=dominant_reason,
        dominant_reason_percentage=(
            dominant_percentage
        ),
    )

async def calculate_dashboard_overview(
    db: AsyncSession,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> DashboardOverviewMetrics:
    validate_dashboard_period(
        start_at,
        end_at,
    )

    production_lines = await get_production_lines(
        db
    )

    line_metrics: list[
        DashboardProductionLineMetrics
    ] = []

    all_completed_runs: list[
        ProductionRun
    ] = []

    for production_line in production_lines:
        completed_runs = (
            await get_completed_runs_for_line(
                db,
                production_line.id,
                start_at=start_at,
                end_at=end_at,
            )
        )

        all_completed_runs.extend(
            completed_runs
        )

        if not completed_runs:
            line_metrics.append(
                DashboardProductionLineMetrics(
                    id=production_line.id,
                    name=production_line.name,
                    code=production_line.code,
                    oee=None,
                    availability=None,
                )
            )

            continue

        try:
            metrics = (
                await calculate_aggregated_oee_for_runs(
                    db,
                    completed_runs,
                )
            )
        except ProductionAnalyticsServiceError as exc:
            raise DashboardServiceError(
                str(exc)
            ) from exc

        line_metrics.append(
            DashboardProductionLineMetrics(
                id=production_line.id,
                name=production_line.name,
                code=production_line.code,
                oee=metrics.oee,
                availability=metrics.availability,
            )
        )

    overall_metrics: (
        AggregatedOEEMetrics | None
    ) = None

    if all_completed_runs:
        try:
            overall_metrics = (
                await calculate_aggregated_oee_for_runs(
                    db,
                    all_completed_runs,
                )
            )
        except ProductionAnalyticsServiceError as exc:
            raise DashboardServiceError(
                str(exc)
            ) from exc

    active_alert_count = (
        await get_active_alert_count(db)
    )

    fleet_mtbf_seconds = (
        await calculate_fleet_mtbf(
            db,
            start_at=start_at,
            end_at=end_at,
        )
    )

    machine_health = (
        await calculate_machine_health(db)
    )

    recent_alerts = (
        await get_recent_open_alerts(
            db,
            limit=3,
        )
    )
    needs_attention = (
        await calculate_factory_needs_attention(
            db,
            start_at=start_at,
            end_at=end_at,
        )
    )

    return DashboardOverviewMetrics(
        start_at=start_at,
        end_at=end_at,
        overall_oee=(
            overall_metrics.oee
            if overall_metrics is not None
            else None
        ),
        availability=(
            overall_metrics.availability
            if overall_metrics is not None
            else None
        ),
        active_alert_count=(
            active_alert_count
        ),
        fleet_mtbf_seconds=(
            fleet_mtbf_seconds
        ),
        production_lines=line_metrics,
        machine_health=machine_health,
        recent_alerts=recent_alerts,
        needs_attention=needs_attention,
    )