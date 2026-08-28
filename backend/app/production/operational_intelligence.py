from dataclasses import dataclass
from typing import Sequence

from app.production.downtime_analytics import (
    DowntimeAnalyticsMetrics,
)


class OperationalIntelligenceError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class MachineReliabilitySnapshot:
    machine_id: int
    machine_name: str
    machine_code: str

    failure_count: int
    mttr_seconds: float | None
    operating_exposure_seconds: float | None
    mtbf_seconds: float | None


@dataclass(frozen=True, slots=True)
class MachineOperationalImpact:
    machine_id: int
    machine_name: str
    machine_code: str

    recorded_downtime_event_count: int
    recorded_downtime_seconds: float
    recorded_downtime_share: float | None

    failure_count: int
    mttr_seconds: float | None
    operating_exposure_seconds: float | None
    mtbf_seconds: float | None


@dataclass(frozen=True, slots=True)
class OperationalDowntimeSummary:
    recorded_downtime_seconds: float

    machine_attributed_recorded_downtime_seconds: float
    unattributed_recorded_downtime_seconds: float

    machine_attributed_share: float | None
    unattributed_share: float | None

    top_downtime_machine_id: int | None

    machines: tuple[
        MachineOperationalImpact,
        ...,
    ]


def calculate_operational_downtime_impact(
    downtime_metrics: DowntimeAnalyticsMetrics,
    machines: Sequence[MachineReliabilitySnapshot],
) -> OperationalDowntimeSummary:
    machine_ids = [
        machine.machine_id
        for machine in machines
    ]

    if len(machine_ids) != len(set(machine_ids)):
        raise OperationalIntelligenceError(
            "Machine IDs must be unique"
        )

    breakdown_by_machine = {
        breakdown.machine_id: breakdown
        for breakdown in downtime_metrics.by_machine
    }

    machine_impacts: list[
        MachineOperationalImpact
    ] = []

    for machine in machines:
        breakdown = breakdown_by_machine.get(
            machine.machine_id
        )

        if breakdown is None:
            event_count = 0
            duration_seconds = 0.0

            if downtime_metrics.recorded_downtime_seconds > 0:
                downtime_share: float | None = 0.0
            else:
                downtime_share = None
        else:
            event_count = breakdown.event_count
            duration_seconds = breakdown.duration_seconds
            downtime_share = breakdown.percentage

        machine_impacts.append(
            MachineOperationalImpact(
                machine_id=machine.machine_id,
                machine_name=machine.machine_name,
                machine_code=machine.machine_code,
                recorded_downtime_event_count=(
                    event_count
                ),
                recorded_downtime_seconds=(
                    duration_seconds
                ),
                recorded_downtime_share=(
                    downtime_share
                ),
                failure_count=machine.failure_count,
                mttr_seconds=machine.mttr_seconds,
                operating_exposure_seconds=(
                    machine.operating_exposure_seconds
                ),
                mtbf_seconds=machine.mtbf_seconds,
            )
        )

    machine_impacts.sort(
        key=lambda item: (
            -item.recorded_downtime_seconds,
            -item.failure_count,
            item.machine_code.casefold(),
            item.machine_id,
        )
    )

    machine_attributed_seconds = sum(
        breakdown.duration_seconds
        for breakdown in downtime_metrics.by_machine
        if breakdown.machine_id is not None
    )

    unattributed_breakdown = (
        breakdown_by_machine.get(None)
    )

    unattributed_seconds = (
        unattributed_breakdown.duration_seconds
        if unattributed_breakdown is not None
        else 0.0
    )

    recorded_downtime_seconds = (
        downtime_metrics.recorded_downtime_seconds
    )

    if recorded_downtime_seconds > 0:
        machine_attributed_share = (
            machine_attributed_seconds
            / recorded_downtime_seconds
        )

        unattributed_share = (
            unattributed_seconds
            / recorded_downtime_seconds
        )
    else:
        machine_attributed_share = None
        unattributed_share = None

    top_downtime_machine_id = None

    if (
        machine_impacts
        and machine_impacts[0].recorded_downtime_seconds > 0
    ):
        top_downtime_machine_id = (
            machine_impacts[0].machine_id
        )

    return OperationalDowntimeSummary(
        recorded_downtime_seconds=(
            recorded_downtime_seconds
        ),
        machine_attributed_recorded_downtime_seconds=(
            machine_attributed_seconds
        ),
        unattributed_recorded_downtime_seconds=(
            unattributed_seconds
        ),
        machine_attributed_share=(
            machine_attributed_share
        ),
        unattributed_share=unattributed_share,
        top_downtime_machine_id=(
            top_downtime_machine_id
        ),
        machines=tuple(machine_impacts),
    )