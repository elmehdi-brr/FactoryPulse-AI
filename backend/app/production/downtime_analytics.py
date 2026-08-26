from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Sequence


DowntimeCategory = Literal[
    "planned",
    "unplanned",
]


class DowntimeAnalyticsError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class DowntimeAnalyticsEvent:
    reason: str
    category: DowntimeCategory

    started_at: datetime
    ended_at: datetime | None

    machine_id: int | None = None


@dataclass(frozen=True, slots=True)
class DowntimeReasonBreakdown:
    reason: str

    event_count: int
    duration_seconds: float
    percentage: float


@dataclass(frozen=True, slots=True)
class DowntimeMachineBreakdown:
    machine_id: int | None

    event_count: int
    duration_seconds: float
    percentage: float


@dataclass(frozen=True, slots=True)
class DowntimeAnalyticsMetrics:
    event_count: int

    recorded_downtime_seconds: float

    planned_downtime_seconds: float
    unplanned_downtime_seconds: float

    by_reason: tuple[
        DowntimeReasonBreakdown,
        ...
    ]

    by_machine: tuple[
        DowntimeMachineBreakdown,
        ...
    ]


def calculate_downtime_analytics(
    events: Sequence[DowntimeAnalyticsEvent],
) -> DowntimeAnalyticsMetrics:
    if not events:
        return DowntimeAnalyticsMetrics(
            event_count=0,
            recorded_downtime_seconds=0.0,
            planned_downtime_seconds=0.0,
            unplanned_downtime_seconds=0.0,
            by_reason=(),
            by_machine=(),
        )

    reason_data: dict[
        str,
        dict[str, float | int | str],
    ] = {}

    machine_data: dict[
        int | None,
        dict[str, float | int],
    ] = {}

    planned_downtime_seconds = 0.0
    unplanned_downtime_seconds = 0.0

    for event in events:
        if event.category not in {
            "planned",
            "unplanned",
        }:
            raise DowntimeAnalyticsError(
                "Unsupported downtime category"
            )

        if event.ended_at is None:
            raise DowntimeAnalyticsError(
                "Open downtime events cannot be used "
                "for downtime analytics"
            )

        if event.ended_at < event.started_at:
            raise DowntimeAnalyticsError(
                "Downtime ended_at cannot be earlier "
                "than started_at"
            )

        duration_seconds = (
            event.ended_at - event.started_at
        ).total_seconds()

        cleaned_reason = event.reason.strip()

        if not cleaned_reason:
            cleaned_reason = "Unspecified"

        reason_key = cleaned_reason.casefold()

        if reason_key not in reason_data:
            reason_data[reason_key] = {
                "reason": cleaned_reason,
                "event_count": 0,
                "duration_seconds": 0.0,
            }

        reason_data[reason_key]["event_count"] += 1
        reason_data[reason_key]["duration_seconds"] += (
            duration_seconds
        )

        if event.machine_id not in machine_data:
            machine_data[event.machine_id] = {
                "event_count": 0,
                "duration_seconds": 0.0,
            }

        machine_data[event.machine_id][
            "event_count"
        ] += 1

        machine_data[event.machine_id][
            "duration_seconds"
        ] += duration_seconds

        if event.category == "planned":
            planned_downtime_seconds += duration_seconds
        else:
            unplanned_downtime_seconds += duration_seconds

    recorded_downtime_seconds = (
        planned_downtime_seconds
        + unplanned_downtime_seconds
    )

    if recorded_downtime_seconds <= 0:
        raise DowntimeAnalyticsError(
            "Recorded downtime must be greater than zero"
        )

    reason_breakdown = [
        DowntimeReasonBreakdown(
            reason=str(values["reason"]),
            event_count=int(values["event_count"]),
            duration_seconds=float(
                values["duration_seconds"]
            ),
            percentage=(
                float(values["duration_seconds"])
                / recorded_downtime_seconds
            ),
        )
        for values in reason_data.values()
    ]

    reason_breakdown.sort(
        key=lambda item: (
            -item.duration_seconds,
            item.reason.casefold(),
        )
    )

    machine_breakdown = [
        DowntimeMachineBreakdown(
            machine_id=machine_id,
            event_count=int(values["event_count"]),
            duration_seconds=float(
                values["duration_seconds"]
            ),
            percentage=(
                float(values["duration_seconds"])
                / recorded_downtime_seconds
            ),
        )
        for machine_id, values in machine_data.items()
    ]

    machine_breakdown.sort(
        key=lambda item: (
            -item.duration_seconds,
            item.machine_id is None,
            item.machine_id
            if item.machine_id is not None
            else 0,
        )
    )

    return DowntimeAnalyticsMetrics(
        event_count=len(events),
        recorded_downtime_seconds=(
            recorded_downtime_seconds
        ),
        planned_downtime_seconds=(
            planned_downtime_seconds
        ),
        unplanned_downtime_seconds=(
            unplanned_downtime_seconds
        ),
        by_reason=tuple(reason_breakdown),
        by_machine=tuple(machine_breakdown),
    )