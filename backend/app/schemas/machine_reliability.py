from datetime import datetime

from pydantic import BaseModel


class MachineReliabilityResponse(BaseModel):
    machine_id: int

    start_at: datetime | None
    end_at: datetime | None

    failure_count: int
    total_failure_downtime_seconds: float
    mttr_seconds: float | None