from datetime import datetime, timezone

import pytest

from app.production.oee import (
    DowntimeWindow,
    OEECalculationError,
    calculate_oee,
)


def dt(hour: int, minute: int = 0) -> datetime:
    return datetime(
        2026,
        8,
        25,
        hour,
        minute,
        tzinfo=timezone.utc,
    )


def test_calculate_oee_without_downtime() -> None:
    metrics = calculate_oee(
        started_at=dt(8),
        ended_at=dt(10),
        ideal_cycle_time_seconds=6.0,
        total_quantity=1000,
        good_quantity=950,
        downtime_windows=[],
    )

    assert metrics.scheduled_time_seconds == 7200
    assert metrics.planned_downtime_seconds == 0
    assert metrics.planned_production_time_seconds == 7200
    assert metrics.unplanned_downtime_seconds == 0
    assert metrics.operating_time_seconds == 7200

    assert metrics.availability == pytest.approx(1.0)

    assert metrics.performance == pytest.approx(
        6000 / 7200
    )

    assert metrics.quality == pytest.approx(
        0.95
    )

    assert metrics.oee == pytest.approx(
        (6000 / 7200) * 0.95
    )


def test_calculate_oee_with_planned_and_unplanned_downtime() -> None:
    metrics = calculate_oee(
        started_at=dt(8),
        ended_at=dt(16),
        ideal_cycle_time_seconds=20.0,
        total_quantity=1000,
        good_quantity=950,
        downtime_windows=[
            DowntimeWindow(
                started_at=dt(9),
                ended_at=dt(9, 30),
                category="planned",
            ),
            DowntimeWindow(
                started_at=dt(13),
                ended_at=dt(13, 45),
                category="unplanned",
            ),
        ],
    )

    assert metrics.scheduled_time_seconds == 28800

    assert metrics.planned_downtime_seconds == 1800
    assert metrics.planned_production_time_seconds == 27000

    assert metrics.unplanned_downtime_seconds == 2700
    assert metrics.operating_time_seconds == 24300

    assert metrics.availability == pytest.approx(
        24300 / 27000
    )

    assert metrics.performance == pytest.approx(
        20000 / 24300
    )

    assert metrics.quality == pytest.approx(
        0.95
    )

    assert metrics.oee == pytest.approx(
        (24300 / 27000)
        * (20000 / 24300)
        * 0.95
    )


def test_overlapping_unplanned_downtime_is_not_double_counted() -> None:
    metrics = calculate_oee(
        started_at=dt(8),
        ended_at=dt(12),
        ideal_cycle_time_seconds=10.0,
        total_quantity=500,
        good_quantity=490,
        downtime_windows=[
            DowntimeWindow(
                started_at=dt(10),
                ended_at=dt(10, 30),
                category="unplanned",
            ),
            DowntimeWindow(
                started_at=dt(10, 15),
                ended_at=dt(10, 45),
                category="unplanned",
            ),
        ],
    )

    # Actual elapsed downtime is 10:00 → 10:45,
    # not 30 + 30 minutes.
    assert metrics.unplanned_downtime_seconds == 2700

    assert metrics.operating_time_seconds == (
        14400 - 2700
    )


def test_planned_and_unplanned_overlap_is_not_double_counted() -> None:
    metrics = calculate_oee(
        started_at=dt(8),
        ended_at=dt(12),
        ideal_cycle_time_seconds=10.0,
        total_quantity=500,
        good_quantity=490,
        downtime_windows=[
            DowntimeWindow(
                started_at=dt(9),
                ended_at=dt(9, 30),
                category="planned",
            ),
            DowntimeWindow(
                started_at=dt(9, 20),
                ended_at=dt(9, 45),
                category="unplanned",
            ),
        ],
    )

    assert metrics.planned_downtime_seconds == 1800

    # Only 09:30 → 09:45 remains as effective
    # unplanned downtime.
    assert metrics.unplanned_downtime_seconds == 900

    assert metrics.planned_production_time_seconds == (
        14400 - 1800
    )

    assert metrics.operating_time_seconds == (
        14400 - 1800 - 900
    )


def test_downtime_outside_run_is_clipped() -> None:
    metrics = calculate_oee(
        started_at=dt(8),
        ended_at=dt(12),
        ideal_cycle_time_seconds=10.0,
        total_quantity=500,
        good_quantity=490,
        downtime_windows=[
            DowntimeWindow(
                started_at=dt(7, 30),
                ended_at=dt(8, 15),
                category="unplanned",
            ),
            DowntimeWindow(
                started_at=dt(11, 45),
                ended_at=dt(12, 30),
                category="unplanned",
            ),
        ],
    )

    # Only 08:00 → 08:15 and 11:45 → 12:00
    # belong to the production run.
    assert metrics.unplanned_downtime_seconds == 1800


def test_zero_production_gives_zero_quality_and_oee() -> None:
    metrics = calculate_oee(
        started_at=dt(8),
        ended_at=dt(10),
        ideal_cycle_time_seconds=5.0,
        total_quantity=0,
        good_quantity=0,
        downtime_windows=[],
    )

    assert metrics.quality == 0.0
    assert metrics.performance == 0.0
    assert metrics.oee == 0.0


def test_performance_is_not_artificially_capped() -> None:
    metrics = calculate_oee(
        started_at=dt(8),
        ended_at=dt(9),
        ideal_cycle_time_seconds=10.0,
        total_quantity=400,
        good_quantity=400,
        downtime_windows=[],
    )

    assert metrics.performance == pytest.approx(
        4000 / 3600
    )

    assert metrics.performance > 1.0
    assert metrics.oee > 1.0


def test_open_downtime_cannot_be_used_for_oee() -> None:
    with pytest.raises(
        OEECalculationError,
        match="Open downtime events cannot be used for OEE",
    ):
        calculate_oee(
            started_at=dt(8),
            ended_at=dt(12),
            ideal_cycle_time_seconds=10.0,
            total_quantity=500,
            good_quantity=490,
            downtime_windows=[
                DowntimeWindow(
                    started_at=dt(10),
                    ended_at=None,
                    category="unplanned",
                )
            ],
        )


def test_oee_requires_positive_ideal_cycle_time() -> None:
    with pytest.raises(
        OEECalculationError,
        match="A positive ideal_cycle_time_seconds is required for OEE",
    ):
        calculate_oee(
            started_at=dt(8),
            ended_at=dt(12),
            ideal_cycle_time_seconds=None,
            total_quantity=500,
            good_quantity=490,
            downtime_windows=[],
        )


def test_good_quantity_cannot_exceed_total_quantity() -> None:
    with pytest.raises(
        OEECalculationError,
        match="good_quantity cannot exceed total_quantity",
    ):
        calculate_oee(
            started_at=dt(8),
            ended_at=dt(12),
            ideal_cycle_time_seconds=10.0,
            total_quantity=100,
            good_quantity=101,
            downtime_windows=[],
        )


def test_run_end_must_be_later_than_start() -> None:
    with pytest.raises(
        OEECalculationError,
        match=(
            "Production run ended_at must be later "
            "than started_at"
        ),
    ):
        calculate_oee(
            started_at=dt(8),
            ended_at=dt(8),
            ideal_cycle_time_seconds=10.0,
            total_quantity=100,
            good_quantity=100,
            downtime_windows=[],
        )