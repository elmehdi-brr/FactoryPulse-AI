from datetime import datetime
from typing import Literal

from pydantic import BaseModel


TrendDirection = Literal[
    "improved",
    "worsened",
    "unchanged",
    "not_comparable",
]


class OperationalTrendPeriodResponse(BaseModel):
    start_at: datetime
    end_at: datetime


class OperationalMetricTrendResponse(BaseModel):
    current_value: float | int | None
    previous_value: float | int | None

    delta: float | None
    direction: TrendDirection


class MachineOperationalTrendResponse(BaseModel):
    machine_id: int
    machine_name: str
    machine_code: str

    recorded_downtime: OperationalMetricTrendResponse
    failure_count: OperationalMetricTrendResponse
    mttr: OperationalMetricTrendResponse
    mtbf: OperationalMetricTrendResponse


class OperationalTrendSummaryResponse(BaseModel):
    oee: OperationalMetricTrendResponse
    availability: OperationalMetricTrendResponse
    performance: OperationalMetricTrendResponse
    quality: OperationalMetricTrendResponse

    recorded_downtime: OperationalMetricTrendResponse
    total_failure_count: OperationalMetricTrendResponse

    machines: list[
        MachineOperationalTrendResponse
    ]


class ProductionLineOperationalTrendsResponse(BaseModel):
    production_line_id: int

    current_period: OperationalTrendPeriodResponse
    previous_period: OperationalTrendPeriodResponse

    trends: OperationalTrendSummaryResponse