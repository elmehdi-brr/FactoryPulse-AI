from datetime import datetime

from pydantic import BaseModel


class DashboardPeriodResponse(BaseModel):
    start_at: datetime | None = None
    end_at: datetime | None = None


class DashboardKPIResponse(BaseModel):
    overall_oee: float | None
    availability: float | None
    active_alert_count: int
    fleet_mtbf_seconds: float | None


class DashboardProductionLineSummaryResponse(BaseModel):
    id: int
    name: str
    code: str

    oee: float | None
    availability: float | None


class DashboardOverviewResponse(BaseModel):
    period: DashboardPeriodResponse
    kpis: DashboardKPIResponse
    production_lines: list[
        DashboardProductionLineSummaryResponse
    ]