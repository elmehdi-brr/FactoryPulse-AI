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


class DashboardMachineHealthResponse(BaseModel):
    total_machines: int
    healthy_count: int
    attention_count: int
    critical_count: int


class DashboardRecentAlertResponse(BaseModel):
    id: int

    machine_id: int
    machine_name: str
    machine_code: str

    severity: str
    title: str
    message: str

    created_at: datetime


class DashboardOverviewResponse(BaseModel):
    period: DashboardPeriodResponse

    kpis: DashboardKPIResponse

    production_lines: list[
        DashboardProductionLineSummaryResponse
    ]

    machine_health: DashboardMachineHealthResponse

    recent_alerts: list[
        DashboardRecentAlertResponse
    ]