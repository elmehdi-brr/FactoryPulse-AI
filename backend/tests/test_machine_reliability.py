from datetime import datetime, timezone

import pytest

from app.production.reliability import (
    MachineFailureEvent,
    MachineReliabilityError,
    calculate_machine_failure_metrics,
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


def test_machine_reliability_calculates_failure_count_and_mttr() -> None:
    metrics = calculate_machine_failure_metrics(
        [
            MachineFailureEvent(
                started_at=dt(8),
                ended_at=dt(8, 30),
            ),
            MachineFailureEvent(
                started_at=dt(10),
                ended_at=dt(11, 30),
            ),
        ]
    )

    assert metrics.failure_count == 2

    assert metrics.total_failure_downtime_seconds == pytest.approx(
        7200
    )

    assert metrics.mttr_seconds == pytest.approx(
        3600
    )


def test_machine_reliability_supports_zero_failures() -> None:
    metrics = calculate_machine_failure_metrics([])

    assert metrics.failure_count == 0
    assert metrics.total_failure_downtime_seconds == 0.0
    assert metrics.mttr_seconds is None


def test_machine_reliability_supports_zero_duration_failure() -> None:
    metrics = calculate_machine_failure_metrics(
        [
            MachineFailureEvent(
                started_at=dt(8),
                ended_at=dt(8),
            )
        ]
    )

    assert metrics.failure_count == 1
    assert metrics.total_failure_downtime_seconds == 0.0
    assert metrics.mttr_seconds == 0.0


def test_machine_reliability_rejects_open_failure() -> None:
    with pytest.raises(
        MachineReliabilityError,
        match=(
            "Open failure events cannot be used "
            "for reliability metrics"
        ),
    ):
        calculate_machine_failure_metrics(
            [
                MachineFailureEvent(
                    started_at=dt(8),
                    ended_at=None,
                )
            ]
        )


def test_machine_reliability_rejects_invalid_time_order() -> None:
    with pytest.raises(
        MachineReliabilityError,
        match=(
            "Failure ended_at cannot be earlier "
            "than started_at"
        ),
    ):
        calculate_machine_failure_metrics(
            [
                MachineFailureEvent(
                    started_at=dt(10),
                    ended_at=dt(9),
                )
            ]
        )