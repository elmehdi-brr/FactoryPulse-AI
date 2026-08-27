from datetime import datetime, timezone

import pytest

from app.production.reliability import (
    MachineFailureEvent,
    MachineReliabilityError,
    calculate_machine_failure_metrics,
    ReliabilityDowntimeWindow,
    calculate_operating_exposure_seconds,
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


def test_mtbf_calculation() -> None:
    from app.production.reliability import calculate_mtbf_seconds

    assert calculate_mtbf_seconds(
        operating_time_seconds=18_000,
        failure_count=2,
    ) == pytest.approx(9000)


def test_mtbf_is_none_when_no_failures() -> None:
    from app.production.reliability import calculate_mtbf_seconds

    assert calculate_mtbf_seconds(
        operating_time_seconds=18_000,
        failure_count=0,
    ) is None


def test_mtbf_rejects_negative_operating_time() -> None:
    from app.production.reliability import calculate_mtbf_seconds

    with pytest.raises(
        MachineReliabilityError,
        match="Operating time cannot be negative",
    ):
        calculate_mtbf_seconds(
            operating_time_seconds=-1,
            failure_count=1,
        )


def test_mtbf_rejects_negative_failure_count() -> None:
    from app.production.reliability import calculate_mtbf_seconds

    with pytest.raises(
        MachineReliabilityError,
        match="Failure count cannot be negative",
    ):
        calculate_mtbf_seconds(
            operating_time_seconds=3600,
            failure_count=-1,
        )



def test_operating_exposure_without_downtime() -> None:
    exposure = calculate_operating_exposure_seconds(
        started_at=dt(8),
        ended_at=dt(12),
        downtime_windows=[],
    )

    assert exposure == pytest.approx(
        4 * 3600
    )


def test_operating_exposure_merges_overlapping_downtime() -> None:
    exposure = calculate_operating_exposure_seconds(
        started_at=dt(8),
        ended_at=dt(12),
        downtime_windows=[
            ReliabilityDowntimeWindow(
                started_at=dt(9),
                ended_at=dt(10),
            ),
            ReliabilityDowntimeWindow(
                started_at=dt(9, 30),
                ended_at=dt(10, 30),
            ),
        ],
    )

    assert exposure == pytest.approx(
        2.5 * 3600
    )


def test_operating_exposure_clips_downtime_to_run_boundaries() -> None:
    exposure = calculate_operating_exposure_seconds(
        started_at=dt(8),
        ended_at=dt(12),
        downtime_windows=[
            ReliabilityDowntimeWindow(
                started_at=dt(7),
                ended_at=dt(9),
            ),
            ReliabilityDowntimeWindow(
                started_at=dt(11),
                ended_at=dt(13),
            ),
        ],
    )

    assert exposure == pytest.approx(
        2 * 3600
    )


def test_operating_exposure_rejects_open_downtime() -> None:
    with pytest.raises(
        MachineReliabilityError,
        match=(
            "Open downtime events cannot be used "
            "for operating exposure"
        ),
    ):
        calculate_operating_exposure_seconds(
            started_at=dt(8),
            ended_at=dt(12),
            downtime_windows=[
                ReliabilityDowntimeWindow(
                    started_at=dt(9),
                    ended_at=None,
                )
            ],
        )


def test_operating_exposure_rejects_invalid_run_range() -> None:
    with pytest.raises(
        MachineReliabilityError,
        match=(
            "Production run ended_at must be later "
            "than started_at"
        ),
    ):
        calculate_operating_exposure_seconds(
            started_at=dt(12),
            ended_at=dt(8),
            downtime_windows=[],
        )