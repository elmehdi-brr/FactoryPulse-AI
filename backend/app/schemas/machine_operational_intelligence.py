from datetime import datetime
from typing import Literal

from pydantic import BaseModel


MachineHealthStatus = Literal[
    "healthy",
    "attention",
    "critical",
]


class MachineOperationalImpactResponse(BaseModel):
    recorded_downtime_event_count: int
    recorded_downtime_seconds: float
    recorded_downtime_share: float | None


class MachineOperationalPriorityResponse(BaseModel):
    priority_rank: int | None
    downtime_rank: int | None
    failure_rank: int | None
    mttr_rank: int | None
    mtbf_rank: int | None


class MachineOperationalIntelligenceResponse(BaseModel):
    machine_id: int

    start_at: datetime | None
    end_at: datetime | None

    health_status: MachineHealthStatus

    open_alert_count: int
    critical_alert_count: int
    attention_alert_count: int

    production_line_id: int | None

    failure_count: int
    total_failure_downtime_seconds: float
    mttr_seconds: float | None

    operating_exposure_seconds: float | None
    mtbf_seconds: float | None

    operational_impact: MachineOperationalImpactResponse | None
    operational_priority: MachineOperationalPriorityResponse | None