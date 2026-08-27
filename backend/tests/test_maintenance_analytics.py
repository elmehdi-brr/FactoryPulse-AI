import pytest

from app.maintenance.analytics import (
    MaintenanceAnalyticsError,
    MaintenanceRecordSnapshot,
    calculate_maintenance_effectiveness,
)


def test_calculates_maintenance_effectiveness_metrics() -> None:
    metrics = calculate_maintenance_effectiveness(
        [
            MaintenanceRecordSnapshot(
                maintenance_type="preventive",
                status="completed",
                alert_id=None,
                performed_by_user_id=1,
            ),
            MaintenanceRecordSnapshot(
                maintenance_type="corrective",
                status="verified",
                alert_id=10,
                performed_by_user_id=2,
            ),
            MaintenanceRecordSnapshot(
                maintenance_type="preventive",
                status="planned",
            ),
            MaintenanceRecordSnapshot(
                maintenance_type="corrective",
                status="cancelled",
                alert_id=11,
            ),
        ]
    )

    assert metrics.total_records == 4

    assert metrics.preventive_count == 2
    assert metrics.corrective_count == 2
    assert metrics.preventive_share == pytest.approx(0.5)

    assert metrics.planned_count == 1
    assert metrics.in_progress_count == 0
    assert metrics.completed_count == 1
    assert metrics.verified_count == 1
    assert metrics.cancelled_count == 1

    assert metrics.finished_count == 2

    # Two finished interventions out of three
    # non-cancelled interventions.
    assert metrics.completion_rate == pytest.approx(
        2 / 3
    )

    # One of the two finished interventions is verified.
    assert metrics.verification_rate == pytest.approx(
        0.5
    )

    assert metrics.alert_linked_count == 2
    assert metrics.alert_link_rate == pytest.approx(
        0.5
    )

    assert metrics.assigned_count == 2
    assert metrics.assignment_rate == pytest.approx(
        0.5
    )


def test_empty_maintenance_history_returns_nullable_rates() -> None:
    metrics = calculate_maintenance_effectiveness([])

    assert metrics.total_records == 0
    assert metrics.finished_count == 0

    assert metrics.preventive_share is None
    assert metrics.completion_rate is None
    assert metrics.verification_rate is None
    assert metrics.alert_link_rate is None
    assert metrics.assignment_rate is None


def test_all_cancelled_records_have_no_completion_rate() -> None:
    metrics = calculate_maintenance_effectiveness(
        [
            MaintenanceRecordSnapshot(
                maintenance_type="preventive",
                status="cancelled",
            ),
            MaintenanceRecordSnapshot(
                maintenance_type="corrective",
                status="cancelled",
            ),
        ]
    )

    assert metrics.cancelled_count == 2
    assert metrics.finished_count == 0
    assert metrics.completion_rate is None


def test_rejects_invalid_maintenance_type() -> None:
    with pytest.raises(
        MaintenanceAnalyticsError,
        match="Invalid maintenance type",
    ):
        calculate_maintenance_effectiveness(
            [
                MaintenanceRecordSnapshot(
                    maintenance_type="inspection",
                    status="planned",
                )
            ]
        )


def test_rejects_invalid_maintenance_status() -> None:
    with pytest.raises(
        MaintenanceAnalyticsError,
        match="Invalid maintenance status",
    ):
        calculate_maintenance_effectiveness(
            [
                MaintenanceRecordSnapshot(
                    maintenance_type="preventive",
                    status="done",
                )
            ]
        )