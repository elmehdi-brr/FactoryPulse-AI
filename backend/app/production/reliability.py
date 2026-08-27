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