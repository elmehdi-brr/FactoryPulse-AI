from dataclasses import dataclass
from datetime import datetime
from typing import Sequence


class MachineReliabilityError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class MachineFailureEvent:
    started_at: datetime
    ended_at: datetime | None

@dataclass(frozen=True, slots=True)
class ReliabilityDowntimeWindow:
    started_at: datetime
    ended_at: datetime | None

@dataclass(frozen=True, slots=True)
class MachineReliabilityMetrics:
    failure_count: int
    total_failure_downtime_seconds: float
    mttr_seconds: float | None

    operating_exposure_seconds: float | None
    mtbf_seconds: float | None


@dataclass(frozen=True, slots=True)
class MachineFailureMetrics:
    failure_count: int
    total_failure_downtime_seconds: float
    mttr_seconds: float | None


def calculate_machine_failure_metrics(
    failures: Sequence[MachineFailureEvent],
) -> MachineFailureMetrics:
    if not failures:
        return MachineFailureMetrics(
            failure_count=0,
            total_failure_downtime_seconds=0.0,
            mttr_seconds=None,
        )

    total_failure_downtime_seconds = 0.0

    for failure in failures:
        if failure.ended_at is None:
            raise MachineReliabilityError(
                "Open failure events cannot be used "
                "for reliability metrics"
            )

        if failure.ended_at < failure.started_at:
            raise MachineReliabilityError(
                "Failure ended_at cannot be earlier "
                "than started_at"
            )

        total_failure_downtime_seconds += (
            failure.ended_at - failure.started_at
        ).total_seconds()

    failure_count = len(failures)

    mttr_seconds = (
        total_failure_downtime_seconds
        / failure_count
    )

    return MachineFailureMetrics(
        failure_count=failure_count,
        total_failure_downtime_seconds=(
            total_failure_downtime_seconds
        ),
        mttr_seconds=mttr_seconds,
    )

def calculate_mtbf_seconds(
    operating_time_seconds: float,
    failure_count: int,
) -> float | None:
    if operating_time_seconds < 0:
        raise MachineReliabilityError(
            "Operating time cannot be negative"
        )

    if failure_count < 0:
        raise MachineReliabilityError(
            "Failure count cannot be negative"
        )

    if failure_count == 0:
        return None

    return operating_time_seconds / failure_count



def calculate_operating_exposure_seconds(
    started_at: datetime,
    ended_at: datetime,
    downtime_windows: Sequence[ReliabilityDowntimeWindow],
) -> float:
    if ended_at <= started_at:
        raise MachineReliabilityError(
            "Production run ended_at must be later than started_at"
        )

    intervals: list[tuple[datetime, datetime]] = []

    for downtime in downtime_windows:
        if downtime.ended_at is None:
            raise MachineReliabilityError(
                "Open downtime events cannot be used "
                "for operating exposure"
            )

        if downtime.ended_at < downtime.started_at:
            raise MachineReliabilityError(
                "Downtime ended_at cannot be earlier "
                "than started_at"
            )

        clipped_start = max(
            started_at,
            downtime.started_at,
        )

        clipped_end = min(
            ended_at,
            downtime.ended_at,
        )

        if clipped_end <= clipped_start:
            continue

        intervals.append(
            (
                clipped_start,
                clipped_end,
            )
        )

    intervals.sort(
        key=lambda interval: interval[0]
    )

    merged_intervals: list[
        tuple[datetime, datetime]
    ] = []

    for interval_start, interval_end in intervals:
        if not merged_intervals:
            merged_intervals.append(
                (
                    interval_start,
                    interval_end,
                )
            )
            continue

        previous_start, previous_end = (
            merged_intervals[-1]
        )

        if interval_start <= previous_end:
            merged_intervals[-1] = (
                previous_start,
                max(
                    previous_end,
                    interval_end,
                ),
            )
        else:
            merged_intervals.append(
                (
                    interval_start,
                    interval_end,
                )
            )

    downtime_seconds = sum(
        (
            interval_end - interval_start
        ).total_seconds()
        for interval_start, interval_end
        in merged_intervals
    )

    scheduled_seconds = (
        ended_at - started_at
    ).total_seconds()

    return max(
        0.0,
        scheduled_seconds - downtime_seconds,
    )


def calculate_machine_reliability_metrics(
    failures: Sequence[MachineFailureEvent],
    operating_exposure_seconds: float | None,
) -> MachineReliabilityMetrics:
    failure_metrics = calculate_machine_failure_metrics(
        failures
    )

    if operating_exposure_seconds is None:
        mtbf_seconds = None
    else:
        mtbf_seconds = calculate_mtbf_seconds(
            operating_time_seconds=operating_exposure_seconds,
            failure_count=failure_metrics.failure_count,
        )

    return MachineReliabilityMetrics(
        failure_count=failure_metrics.failure_count,
        total_failure_downtime_seconds=(
            failure_metrics.total_failure_downtime_seconds
        ),
        mttr_seconds=failure_metrics.mttr_seconds,
        operating_exposure_seconds=(
            operating_exposure_seconds
        ),
        mtbf_seconds=mtbf_seconds,
    )