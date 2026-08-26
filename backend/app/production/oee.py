from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Sequence


DowntimeCategory = Literal[
    "planned",
    "unplanned",
]


class OEECalculationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class DowntimeWindow:
    started_at: datetime
    ended_at: datetime | None
    category: DowntimeCategory


@dataclass(frozen=True, slots=True)
class OEEMetrics:
    scheduled_time_seconds: float

    planned_downtime_seconds: float
    planned_production_time_seconds: float

    unplanned_downtime_seconds: float
    operating_time_seconds: float

    availability: float
    performance: float
    quality: float
    oee: float


def _merge_intervals(
    intervals: list[tuple[datetime, datetime]],
) -> list[tuple[datetime, datetime]]:
    if not intervals:
        return []

    sorted_intervals = sorted(
        intervals,
        key=lambda interval: interval[0],
    )

    merged: list[list[datetime]] = [
        [
            sorted_intervals[0][0],
            sorted_intervals[0][1],
        ]
    ]

    for started_at, ended_at in sorted_intervals[1:]:
        current = merged[-1]

        if started_at <= current[1]:
            if ended_at > current[1]:
                current[1] = ended_at

            continue

        merged.append(
            [
                started_at,
                ended_at,
            ]
        )

    return [
        (started_at, ended_at)
        for started_at, ended_at in merged
    ]


def _calculate_interval_seconds(
    intervals: Sequence[
        tuple[datetime, datetime]
    ],
) -> float:
    return sum(
        (ended_at - started_at).total_seconds()
        for started_at, ended_at in intervals
    )


def calculate_oee(
    *,
    started_at: datetime,
    ended_at: datetime,
    ideal_cycle_time_seconds: float | None,
    total_quantity: int,
    good_quantity: int,
    downtime_windows: Sequence[DowntimeWindow],
) -> OEEMetrics:
    if ended_at <= started_at:
        raise OEECalculationError(
            "Production run ended_at must be later than started_at"
        )

    if (
        ideal_cycle_time_seconds is None
        or ideal_cycle_time_seconds <= 0
    ):
        raise OEECalculationError(
            "A positive ideal_cycle_time_seconds is required for OEE"
        )

    if total_quantity < 0:
        raise OEECalculationError(
            "total_quantity cannot be negative"
        )

    if good_quantity < 0:
        raise OEECalculationError(
            "good_quantity cannot be negative"
        )

    if good_quantity > total_quantity:
        raise OEECalculationError(
            "good_quantity cannot exceed total_quantity"
        )

    planned_intervals: list[
        tuple[datetime, datetime]
    ] = []

    all_downtime_intervals: list[
        tuple[datetime, datetime]
    ] = []

    for downtime in downtime_windows:
        if downtime.category not in {
            "planned",
            "unplanned",
        }:
            raise OEECalculationError(
                "Unsupported downtime category"
            )

        if downtime.ended_at is None:
            raise OEECalculationError(
                "Open downtime events cannot be used for OEE"
            )

        if downtime.ended_at < downtime.started_at:
            raise OEECalculationError(
                "Downtime ended_at cannot be earlier than started_at"
            )

        clipped_start = max(
            downtime.started_at,
            started_at,
        )

        clipped_end = min(
            downtime.ended_at,
            ended_at,
        )

        if clipped_end <= clipped_start:
            continue

        interval = (
            clipped_start,
            clipped_end,
        )

        all_downtime_intervals.append(
            interval
        )

        if downtime.category == "planned":
            planned_intervals.append(
                interval
            )

    merged_planned_intervals = _merge_intervals(
        planned_intervals
    )

    merged_all_downtime_intervals = _merge_intervals(
        all_downtime_intervals
    )

    scheduled_time_seconds = (
        ended_at - started_at
    ).total_seconds()

    planned_downtime_seconds = (
        _calculate_interval_seconds(
            merged_planned_intervals
        )
    )

    total_downtime_seconds = (
        _calculate_interval_seconds(
            merged_all_downtime_intervals
        )
    )

    planned_production_time_seconds = (
        scheduled_time_seconds
        - planned_downtime_seconds
    )

    if planned_production_time_seconds <= 0:
        raise OEECalculationError(
            "Planned production time must be greater than zero"
        )

    # Any overlap between planned and unplanned downtime
    # is counted only once. Planned downtime takes priority
    # because it is excluded from planned production time.
    unplanned_downtime_seconds = max(
        0.0,
        total_downtime_seconds
        - planned_downtime_seconds,
    )

    operating_time_seconds = max(
        0.0,
        planned_production_time_seconds
        - unplanned_downtime_seconds,
    )

    availability = (
        operating_time_seconds
        / planned_production_time_seconds
    )

    if operating_time_seconds == 0:
        performance = 0.0
    else:
        performance = (
            ideal_cycle_time_seconds
            * total_quantity
            / operating_time_seconds
        )

    if total_quantity == 0:
        quality = 0.0
    else:
        quality = (
            good_quantity
            / total_quantity
        )

    oee = (
        availability
        * performance
        * quality
    )

    return OEEMetrics(
        scheduled_time_seconds=scheduled_time_seconds,
        planned_downtime_seconds=planned_downtime_seconds,
        planned_production_time_seconds=(
            planned_production_time_seconds
        ),
        unplanned_downtime_seconds=(
            unplanned_downtime_seconds
        ),
        operating_time_seconds=operating_time_seconds,
        availability=availability,
        performance=performance,
        quality=quality,
        oee=oee,
    )