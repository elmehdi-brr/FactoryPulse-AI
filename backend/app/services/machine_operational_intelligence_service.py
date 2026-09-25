from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.machine import Machine
from app.models.sensor import Sensor
from app.production.operational_intelligence import (
    MachineOperationalImpact,
    MachineOperationalPriority,
    calculate_machine_health_status,
)
from app.services.machine_reliability_service import (
    MachineReliabilityServiceError,
    calculate_machine_reliability,
)
from app.services.production_analytics_service import (
    get_completed_runs_for_line,
)
from app.services.operational_intelligence_service import (
    OperationalIntelligenceServiceError,
    calculate_production_line_operational_intelligence,
)


class MachineOperationalIntelligenceServiceError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class MachineAlertSummary:
    open_alert_count: int
    critical_alert_count: int
    attention_alert_count: int


@dataclass(frozen=True, slots=True)
class MachineOperationalIntelligenceResult:
    machine_id: int

    start_at: datetime | None
    end_at: datetime | None

    health_status: str

    alerts: MachineAlertSummary

    production_line_id: int | None

    failure_count: int
    total_failure_downtime_seconds: float
    mttr_seconds: float | None

    operating_exposure_seconds: float | None
    mtbf_seconds: float | None

    operational_impact: MachineOperationalImpact | None
    operational_priority: MachineOperationalPriority | None


async def get_machine_alert_summary(
    db: AsyncSession,
    machine_id: int,
) -> MachineAlertSummary:
    result = await db.execute(
        select(Alert.severity)
        .join(
            Sensor,
            Alert.sensor_id == Sensor.id,
        )
        .where(
            Sensor.machine_id == machine_id,
            Alert.status == "open",
        )
    )

    severities = list(result.scalars().all())

    critical_count = sum(
        severity.strip().lower() == "critical"
        for severity in severities
    )

    open_alert_count = len(severities)

    return MachineAlertSummary(
        open_alert_count=open_alert_count,
        critical_alert_count=critical_count,
        attention_alert_count=(
            open_alert_count - critical_count
        ),
    )


async def calculate_machine_operational_intelligence(
    db: AsyncSession,
    machine_id: int,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> MachineOperationalIntelligenceResult:
    machine_result = await db.execute(
        select(Machine).where(
            Machine.id == machine_id
        )
    )

    machine = machine_result.scalar_one_or_none()

    if machine is None:
        raise MachineOperationalIntelligenceServiceError(
            "Machine not found"
        )

    alerts = await get_machine_alert_summary(
        db,
        machine_id,
    )

    alert_severities: list[str] = []

    if alerts.critical_alert_count > 0:
        alert_severities.extend(
            ["critical"] * alerts.critical_alert_count
        )

    alert_severities.extend(
        ["attention"] * alerts.attention_alert_count
    )

    health_status = calculate_machine_health_status(
        alert_severities
    )

    try:
        reliability = await calculate_machine_reliability(
            db,
            machine_id,
            start_at=start_at,
            end_at=end_at,
        )
    except MachineReliabilityServiceError as exc:
        raise MachineOperationalIntelligenceServiceError(
            str(exc)
        ) from exc

    operational_impact = None
    operational_priority = None

    if machine.production_line_id is not None:
        completed_runs = await get_completed_runs_for_line(
            db,
            machine.production_line_id,
            start_at=start_at,
            end_at=end_at,
        )

        if completed_runs:
            try:
                intelligence = (
                    await calculate_production_line_operational_intelligence(
                        db,
                        machine.production_line_id,
                        start_at=start_at,
                        end_at=end_at,
                    )
                )
            except OperationalIntelligenceServiceError as exc:
                raise (
                    MachineOperationalIntelligenceServiceError(
                        str(exc)
                    )
                ) from exc

            operational_impact = next(
                (
                    item
                    for item in (
                        intelligence.operational_impact.machines
                    )
                    if item.machine_id == machine_id
                ),
                None,
            )

            operational_priority = next(
                (
                    item
                    for item in intelligence.priority.machines
                    if item.machine_id == machine_id
                ),
                None,
            )

    return MachineOperationalIntelligenceResult(
        machine_id=machine.id,
        start_at=start_at,
        end_at=end_at,
        health_status=health_status,
        alerts=alerts,
        production_line_id=machine.production_line_id,
        failure_count=reliability.failure_count,
        total_failure_downtime_seconds=(
            reliability.total_failure_downtime_seconds
        ),
        mttr_seconds=reliability.mttr_seconds,
        operating_exposure_seconds=(
            reliability.operating_exposure_seconds
        ),
        mtbf_seconds=reliability.mtbf_seconds,
        operational_impact=operational_impact,
        operational_priority=operational_priority,
    )