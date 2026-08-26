from datetime import datetime

from pydantic import BaseModel


class ProductionLineOEEResponse(BaseModel):
    production_line_id: int

    start_at: datetime | None
    end_at: datetime | None

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