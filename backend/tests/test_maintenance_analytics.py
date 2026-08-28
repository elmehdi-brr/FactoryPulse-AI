import pytest
from datetime import datetime, timezone

from app.maintenance.analytics import (
    MaintenanceAnalyticsError,
    MaintenanceRecordSnapshot,
    calculate_maintenance_effectiveness,
    MaintenanceResponseObservation,
    calculate_maintenance_response_metrics,
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

def test_calculates_maintenance_response_metrics() -> None:
    observations = [
        MaintenanceResponseObservation(
            alert_created_at=datetime(
                2026, 8, 20, 8, 0,
                tzinfo=timezone.utc,
            ),
            maintenance_performed_at=datetime(
                2026, 8, 20, 8, 10,
                tzinfo=timezone.utc,
            ),
        ),
        MaintenanceResponseObservation(
            alert_created_at=datetime(
                2026, 8, 20, 9, 0,
                tzinfo=timezone.utc,
            ),
            maintenance_performed_at=datetime(
                2026, 8, 20, 9, 50,
                tzinfo=timezone.utc,
            ),
        ),
        MaintenanceResponseObservation(
            alert_created_at=datetime(
                2026, 8, 20, 10, 0,
                tzinfo=timezone.utc,
            ),
            maintenance_performed_at=None,
        ),
    ]

    metrics = calculate_maintenance_response_metrics(
        observations
    )

    assert metrics.total_alerts == 3
    assert metrics.responded_alert_count == 2
    assert metrics.unresponded_alert_count == 1
    assert metrics.response_rate == pytest.approx(2 / 3)

    assert metrics.average_response_time_seconds == pytest.approx(
        1800
    )
    assert metrics.median_response_time_seconds == pytest.approx(
        1800
    )
    assert metrics.fastest_response_time_seconds == pytest.approx(
        600
    )
    assert metrics.slowest_response_time_seconds == pytest.approx(
        3000
    )


def test_empty_alert_history_has_nullable_response_rate() -> None:
    metrics = calculate_maintenance_response_metrics([])

    assert metrics.total_alerts == 0
    assert metrics.responded_alert_count == 0
    assert metrics.unresponded_alert_count == 0

    assert metrics.response_rate is None
    assert metrics.average_response_time_seconds is None
    assert metrics.median_response_time_seconds is None


def test_alerts_without_maintenance_have_zero_response_rate() -> None:
    metrics = calculate_maintenance_response_metrics(
        [
            MaintenanceResponseObservation(
                alert_created_at=datetime(
                    2026, 8, 20, 8, 0,
                    tzinfo=timezone.utc,
                ),
                maintenance_performed_at=None,
            )
        ]
    )

    assert metrics.total_alerts == 1
    assert metrics.responded_alert_count == 0
    assert metrics.unresponded_alert_count == 1

    assert metrics.response_rate == pytest.approx(0.0)

    assert metrics.average_response_time_seconds is None
    assert metrics.median_response_time_seconds is None
    assert metrics.fastest_response_time_seconds is None
    assert metrics.slowest_response_time_seconds is None


def test_zero_time_maintenance_response_is_valid() -> None:
    timestamp = datetime(
        2026, 8, 20, 8, 0,
        tzinfo=timezone.utc,
    )

    metrics = calculate_maintenance_response_metrics(
        [
            MaintenanceResponseObservation(
                alert_created_at=timestamp,
                maintenance_performed_at=timestamp,
            )
        ]
    )

    assert metrics.response_rate == pytest.approx(1.0)
    assert metrics.average_response_time_seconds == pytest.approx(
        0.0
    )


def test_rejects_maintenance_response_before_alert() -> None:
    with pytest.raises(
        MaintenanceAnalyticsError,
        match=(
            "Maintenance response cannot occur "
            "before alert creation"
        ),
    ):
        calculate_maintenance_response_metrics(
            [
                MaintenanceResponseObservation(
                    alert_created_at=datetime(
                        2026, 8, 20, 10, 0,
                        tzinfo=timezone.utc,
                    ),
                    maintenance_performed_at=datetime(
                        2026, 8, 20, 9, 0,
                        tzinfo=timezone.utc,
                    ),
                )
            ]
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

    