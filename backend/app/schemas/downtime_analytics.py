from datetime import datetime

from pydantic import BaseModel


class DowntimeReasonBreakdownResponse(BaseModel):
    reason: str

    event_count: int
    duration_seconds: float
    percentage: float


class DowntimeMachineBreakdownResponse(BaseModel):
    machine_id: int | None

    event_count: int
    duration_seconds: float
    percentage: float


class ProductionLineDowntimeAnalyticsResponse(BaseModel):
    production_line_id: int

    start_at: datetime | None
    end_at: datetime | None

    run_count: int
    event_count: int

    recorded_downtime_seconds: float

    planned_downtime_seconds: float
    unplanned_downtime_seconds: float

    by_reason: list[DowntimeReasonBreakdownResponse]
    by_machine: list[DowntimeMachineBreakdownResponse]