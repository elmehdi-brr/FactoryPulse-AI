from dataclasses import dataclass
from typing import Sequence


class MaintenanceAnalyticsError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class MaintenanceRecordSnapshot:
    maintenance_type: str
    status: str
    alert_id: int | None = None
    performed_by_user_id: int | None = None


@dataclass(frozen=True, slots=True)
class MaintenanceEffectivenessMetrics:
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


def calculate_maintenance_effectiveness(
    records: Sequence[MaintenanceRecordSnapshot],
) -> MaintenanceEffectivenessMetrics:
    valid_types = {
        "preventive",
        "corrective",
    }

    valid_statuses = {
        "planned",
        "in_progress",
        "completed",
        "verified",
        "cancelled",
    }

    for record in records:
        if record.maintenance_type not in valid_types:
            raise MaintenanceAnalyticsError(
                "Invalid maintenance type"
            )

        if record.status not in valid_statuses:
            raise MaintenanceAnalyticsError(
                "Invalid maintenance status"
            )

    total_records = len(records)

    preventive_count = sum(
        record.maintenance_type == "preventive"
        for record in records
    )

    corrective_count = sum(
        record.maintenance_type == "corrective"
        for record in records
    )

    planned_count = sum(
        record.status == "planned"
        for record in records
    )

    in_progress_count = sum(
        record.status == "in_progress"
        for record in records
    )

    completed_count = sum(
        record.status == "completed"
        for record in records
    )

    verified_count = sum(
        record.status == "verified"
        for record in records
    )

    cancelled_count = sum(
        record.status == "cancelled"
        for record in records
    )

    finished_count = (
        completed_count
        + verified_count
    )

    non_cancelled_count = (
        total_records
        - cancelled_count
    )

    alert_linked_count = sum(
        record.alert_id is not None
        for record in records
    )

    assigned_count = sum(
        record.performed_by_user_id is not None
        for record in records
    )

    preventive_share = (
        preventive_count / total_records
        if total_records
        else None
    )

    completion_rate = (
        finished_count / non_cancelled_count
        if non_cancelled_count
        else None
    )

    verification_rate = (
        verified_count / finished_count
        if finished_count
        else None
    )

    alert_link_rate = (
        alert_linked_count / total_records
        if total_records
        else None
    )

    assignment_rate = (
        assigned_count / total_records
        if total_records
        else None
    )

    return MaintenanceEffectivenessMetrics(
        total_records=total_records,
        preventive_count=preventive_count,
        corrective_count=corrective_count,
        preventive_share=preventive_share,
        planned_count=planned_count,
        in_progress_count=in_progress_count,
        completed_count=completed_count,
        verified_count=verified_count,
        cancelled_count=cancelled_count,
        finished_count=finished_count,
        completion_rate=completion_rate,
        verification_rate=verification_rate,
        alert_linked_count=alert_linked_count,
        alert_link_rate=alert_link_rate,
        assigned_count=assigned_count,
        assignment_rate=assignment_rate,
    )