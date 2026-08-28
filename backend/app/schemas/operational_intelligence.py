from datetime import datetime

from pydantic import BaseModel


class OperationalMachineImpactResponse(BaseModel):
    machine_id: int
    machine_name: str
    machine_code: str

    recorded_downtime_event_count: int
    recorded_downtime_seconds: float
    recorded_downtime_share: float | None

    failure_count: int
    mttr_seconds: float | None
    operating_exposure_seconds: float | None
    mtbf_seconds: float | None


class OperationalDowntimeSummaryResponse(BaseModel):
    recorded_downtime_seconds: float

    machine_attributed_recorded_downtime_seconds: float
    unattributed_recorded_downtime_seconds: float

    machine_attributed_share: float | None
    unattributed_share: float | None

    top_downtime_machine_id: int | None

    machines: list[OperationalMachineImpactResponse]


class OperationalOEEResponse(BaseModel):
    run_count: int

    scheduled_time_seconds: float

    planned_downtime_seconds: float
    planned_production_time_seconds: float

    unplanned_downtime_seconds: float
    operating_time_seconds: float

    total_quantity: int
    good_quantity: int

    availability: float
    performance: float
    quality: float
    oee: float


class ProductionLineOperationalIntelligenceResponse(BaseModel):
    production_line_id: int

    start_at: datetime | None
    end_at: datetime | None

    run_count: int

    oee: OperationalOEEResponse
    operational_impact: OperationalDowntimeSummaryResponse