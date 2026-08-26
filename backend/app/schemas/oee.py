from pydantic import BaseModel


class OEEResponse(BaseModel):
    production_run_id: int

    scheduled_time_seconds: float

    planned_downtime_seconds: float
    planned_production_time_seconds: float

    unplanned_downtime_seconds: float
    operating_time_seconds: float

    availability: float
    performance: float
    quality: float
    oee: float