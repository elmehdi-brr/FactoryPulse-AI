from datetime import datetime

from pydantic import BaseModel


class MaintenanceEffectivenessResponse(BaseModel):
    machine_id: int

    start_at: datetime | None
    end_at: datetime | None

    total_records: int

    preventive_count: int
    corrective_count: int
    preventive_share: float | None

    planned_count: int
    in_progress_count: int
    completed_count: int
    verified_count: int
    cancelled_count: int

    finished_count: int
    completion_rate: float | None
    verification_rate: float | None

    alert_linked_count: int
    alert_link_rate: float | None

    assigned_count: int
    assignment_rate: float | None

    total_alerts: int
    responded_alert_count: int
    unresponded_alert_count: int
    response_rate: float | None

    average_response_time_seconds: float | None
    median_response_time_seconds: float | None
    fastest_response_time_seconds: float | None
    slowest_response_time_seconds: float | None