from datetime import datetime, timezone

import pytest

from app.production.downtime_analytics import (
    DowntimeAnalyticsError,
    DowntimeAnalyticsEvent,
    calculate_downtime_analytics,
    calculate_machine_downtime_reason_analytics,
)


def dt(
    hour: int,
    minute: int = 0,
) -> datetime:
    return datetime(
        2026,
        8,
        20,
        hour,
        minute,
        tzinfo=timezone.utc,
    )


def test_downtime_analytics_aggregates_and_ranks_reasons() -> None:
    metrics = calculate_downtime_analytics(
        [
            DowntimeAnalyticsEvent(
                reason="Motor Failure",
                category="unplanned",
                started_at=dt(8),
                ended_at=dt(9),
                machine_id=1,
            ),
            DowntimeAnalyticsEvent(
                reason=" motor failure ",
                category="unplanned",
                started_at=dt(10),
                ended_at=dt(10, 30),
                machine_id=1,
            ),
            DowntimeAnalyticsEvent(
                reason="Changeover",
                category="planned",
                started_at=dt(11),
                ended_at=dt(12),
                machine_id=None,
            ),
        ]
    )

    assert metrics.event_count == 3

    assert metrics.recorded_downtime_seconds == pytest.approx(
        9000
    )

    assert metrics.planned_downtime_seconds == pytest.approx(
        3600
    )

    assert metrics.unplanned_downtime_seconds == pytest.approx(
        5400
    )

    assert len(metrics.by_reason) == 2

    motor_failure = metrics.by_reason[0]

    assert motor_failure.reason == "Motor Failure"
    assert motor_failure.event_count == 2
    assert motor_failure.duration_seconds == pytest.approx(
        5400
    )
    assert motor_failure.percentage == pytest.approx(
        5400 / 9000
    )

    changeover = metrics.by_reason[1]

    assert changeover.reason == "Changeover"
    assert changeover.event_count == 1
    assert changeover.duration_seconds == pytest.approx(
        3600
    )
    assert changeover.percentage == pytest.approx(
        3600 / 9000
    )


def test_downtime_analytics_aggregates_by_machine() -> None:
    metrics = calculate_downtime_analytics(
        [
            DowntimeAnalyticsEvent(
                reason="Motor Failure",
                category="unplanned",
                started_at=dt(8),
                ended_at=dt(9),
                machine_id=10,
            ),
            DowntimeAnalyticsEvent(
                reason="Electrical Fault",
                category="unplanned",
                started_at=dt(10),
                ended_at=dt(10, 30),
                machine_id=10,
            ),
            DowntimeAnalyticsEvent(
                reason="Material Shortage",
                category="unplanned",
                started_at=dt(11),
                ended_at=dt(11, 45),
                machine_id=20,
            ),
        ]
    )

    assert len(metrics.by_machine) == 2

    machine_10 = metrics.by_machine[0]

    assert machine_10.machine_id == 10
    assert machine_10.event_count == 2
    assert machine_10.duration_seconds == pytest.approx(
        5400
    )

    machine_20 = metrics.by_machine[1]

    assert machine_20.machine_id == 20
    assert machine_20.event_count == 1
    assert machine_20.duration_seconds == pytest.approx(
        2700
    )


def test_downtime_analytics_supports_line_wide_events() -> None:
    metrics = calculate_downtime_analytics(
        [
            DowntimeAnalyticsEvent(
                reason="Line Cleaning",
                category="planned",
                started_at=dt(8),
                ended_at=dt(9),
                machine_id=None,
            )
        ]
    )

    assert len(metrics.by_machine) == 1

    breakdown = metrics.by_machine[0]

    assert breakdown.machine_id is None
    assert breakdown.event_count == 1
    assert breakdown.duration_seconds == pytest.approx(
        3600
    )
    assert breakdown.percentage == pytest.approx(
        1.0
    )


def test_overlapping_events_are_counted_as_recorded_event_duration() -> None:
    metrics = calculate_downtime_analytics(
        [
            DowntimeAnalyticsEvent(
                reason="Motor Failure",
                category="unplanned",
                started_at=dt(8),
                ended_at=dt(9),
                machine_id=1,
            ),
            DowntimeAnalyticsEvent(
                reason="Electrical Fault",
                category="unplanned",
                started_at=dt(8, 30),
                ended_at=dt(9, 30),
                machine_id=2,
            ),
        ]
    )

    # Actual elapsed downtime from 08:00 to 09:30 is
    # 5400 seconds, but Pareto analytics intentionally
    # measures recorded event duration.
    assert metrics.recorded_downtime_seconds == pytest.approx(
        7200
    )

    assert metrics.unplanned_downtime_seconds == pytest.approx(
        7200
    )


def test_blank_reason_is_grouped_as_unspecified() -> None:
    metrics = calculate_downtime_analytics(
        [
            DowntimeAnalyticsEvent(
                reason="   ",
                category="unplanned",
                started_at=dt(8),
                ended_at=dt(9),
                machine_id=1,
            )
        ]
    )

    assert metrics.by_reason[0].reason == "Unspecified"
    assert metrics.by_reason[0].event_count == 1


def test_downtime_analytics_supports_zero_downtime() -> None:
    metrics = calculate_downtime_analytics([])

    assert metrics.event_count == 0

    assert metrics.recorded_downtime_seconds == 0.0
    assert metrics.planned_downtime_seconds == 0.0
    assert metrics.unplanned_downtime_seconds == 0.0

    assert metrics.by_reason == ()
    assert metrics.by_machine == ()


def test_downtime_analytics_rejects_open_events() -> None:
    with pytest.raises(
        DowntimeAnalyticsError,
        match=(
            "Open downtime events cannot be used "
            "for downtime analytics"
        ),
    ):
        calculate_downtime_analytics(
            [
                DowntimeAnalyticsEvent(
                    reason="Motor Failure",
                    category="unplanned",
                    started_at=dt(8),
                    ended_at=None,
                    machine_id=1,
                )
            ]
        )


def test_downtime_analytics_rejects_invalid_time_range() -> None:
    with pytest.raises(
        DowntimeAnalyticsError,
        match=(
            "Downtime ended_at cannot be earlier "
            "than started_at"
        ),
    ):
        calculate_downtime_analytics(
            [
                DowntimeAnalyticsEvent(
                    reason="Motor Failure",
                    category="unplanned",
                    started_at=dt(9),
                    ended_at=dt(8),
                    machine_id=1,
                )
            ]
        )


def test_downtime_analytics_rejects_zero_recorded_duration() -> None:
    with pytest.raises(
        DowntimeAnalyticsError,
        match="Recorded downtime must be greater than zero",
    ):
        calculate_downtime_analytics(
            [
                DowntimeAnalyticsEvent(
                    reason="Instant Event",
                    category="unplanned",
                    started_at=dt(8),
                    ended_at=dt(8),
                    machine_id=1,
                )
            ]
        )

def test_machine_downtime_reason_analytics_identifies_dominant_reasons() -> None:
    events = [
        DowntimeAnalyticsEvent(
            reason="Motor Overheating",
            category="unplanned",
            started_at=dt(8),
            ended_at=dt(9),
            machine_id=1,
        ),
        DowntimeAnalyticsEvent(
            reason=" motor overheating ",
            category="unplanned",
            started_at=dt(10),
            ended_at=dt(11),
            machine_id=1,
        ),
        DowntimeAnalyticsEvent(
            reason="Bearing Failure",
            category="unplanned",
            started_at=dt(12),
            ended_at=dt(12, 30),
            machine_id=1,
        ),
        DowntimeAnalyticsEvent(
            reason="Bearing Failure",
            category="unplanned",
            started_at=dt(13),
            ended_at=dt(13, 30),
            machine_id=1,
        ),
        DowntimeAnalyticsEvent(
            reason="Bearing Failure",
            category="unplanned",
            started_at=dt(14),
            ended_at=dt(14, 30),
            machine_id=1,
        ),
        DowntimeAnalyticsEvent(
            reason="Other Machine Failure",
            category="unplanned",
            started_at=dt(15),
            ended_at=dt(16),
            machine_id=2,
        ),
    ]

    result = calculate_machine_downtime_reason_analytics(
        events,
        machine_id=1,
    )

    assert result.machine_id == 1
    assert result.event_count == 5

    assert result.recorded_downtime_seconds == pytest.approx(
        3.5 * 3600
    )

    # Motor overheating has the greatest duration:
    # 2h total.
    assert result.dominant_duration_reason == (
        "Motor Overheating"
    )

    # Bearing Failure happens three times.
    assert result.most_frequent_reason == (
        "Bearing Failure"
    )

    assert len(result.by_reason) == 2

    motor = result.by_reason[0]
    bearing = result.by_reason[1]

    assert motor.reason == "Motor Overheating"
    assert motor.event_count == 2

    assert motor.duration_seconds == pytest.approx(
        2 * 3600
    )

    assert motor.percentage == pytest.approx(
        2 / 3.5
    )

    assert motor.unplanned_event_count == 2

    assert motor.unplanned_duration_seconds == pytest.approx(
        2 * 3600
    )

    assert motor.planned_event_count == 0
    assert motor.planned_duration_seconds == 0.0

    assert bearing.reason == "Bearing Failure"
    assert bearing.event_count == 3

    assert bearing.duration_seconds == pytest.approx(
        1.5 * 3600
    )


def test_machine_downtime_reason_analytics_separates_categories() -> None:
    events = [
        DowntimeAnalyticsEvent(
            reason="Maintenance",
            category="planned",
            started_at=dt(8),
            ended_at=dt(9),
            machine_id=1,
        ),
        DowntimeAnalyticsEvent(
            reason="Maintenance",
            category="unplanned",
            started_at=dt(10),
            ended_at=dt(10, 30),
            machine_id=1,
        ),
    ]

    result = calculate_machine_downtime_reason_analytics(
        events,
        machine_id=1,
    )

    maintenance = result.by_reason[0]

    assert maintenance.event_count == 2

    assert maintenance.duration_seconds == pytest.approx(
        1.5 * 3600
    )

    assert maintenance.planned_event_count == 1
    assert maintenance.planned_duration_seconds == pytest.approx(
        1 * 3600
    )

    assert maintenance.unplanned_event_count == 1

    assert (
        maintenance.unplanned_duration_seconds
        == pytest.approx(0.5 * 3600)
    )


def test_machine_downtime_reason_analytics_empty_machine() -> None:
    events = [
        DowntimeAnalyticsEvent(
            reason="Motor Failure",
            category="unplanned",
            started_at=dt(8),
            ended_at=dt(9),
            machine_id=2,
        )
    ]

    result = calculate_machine_downtime_reason_analytics(
        events,
        machine_id=1,
    )

    assert result.event_count == 0
    assert result.recorded_downtime_seconds == 0.0

    assert result.dominant_duration_reason is None
    assert result.most_frequent_reason is None

    assert result.by_reason == ()


def test_machine_downtime_reason_analytics_uses_unspecified_reason() -> None:
    events = [
        DowntimeAnalyticsEvent(
            reason="   ",
            category="unplanned",
            started_at=dt(8),
            ended_at=dt(9),
            machine_id=1,
        )
    ]

    result = calculate_machine_downtime_reason_analytics(
        events,
        machine_id=1,
    )

    assert result.dominant_duration_reason == "Unspecified"
    assert result.most_frequent_reason == "Unspecified"

    assert result.by_reason[0].reason == "Unspecified"