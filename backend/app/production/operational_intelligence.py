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


@dataclass(frozen=True, slots=True)
class MachineOperationalPriority:
    machine_id: int
    machine_name: str
    machine_code: str

    priority_rank: int | None

    downtime_rank: int | None
    failure_rank: int | None
    mttr_rank: int | None
    mtbf_rank: int | None


@dataclass(frozen=True, slots=True)
class OperationalPrioritySummary:
    top_priority_machine_id: int | None

    machines: tuple[
        MachineOperationalPriority,
        ...,
    ]


def _calculate_competition_ranks(
    values: dict[int, float | int],
    *,
    higher_is_worse: bool,
) -> dict[int, int]:
    ordered_values = sorted(
        values.items(),
        key=lambda item: item[1],
        reverse=higher_is_worse,
    )

    ranks: dict[int, int] = {}

    previous_value: float | int | None = None
    current_rank = 0

    for position, (machine_id, value) in enumerate(
        ordered_values,
        start=1,
    ):
        if (
            position == 1
            or value != previous_value
        ):
            current_rank = position

        ranks[machine_id] = current_rank
        previous_value = value

    return ranks


def calculate_operational_priority(
    machines: Sequence[MachineOperationalImpact],
) -> OperationalPrioritySummary:
    machine_ids = [
        machine.machine_id
        for machine in machines
    ]

    if len(machine_ids) != len(set(machine_ids)):
        raise OperationalIntelligenceError(
            "Machine IDs must be unique"
        )

    if not machines:
        return OperationalPrioritySummary(
            top_priority_machine_id=None,
            machines=(),
        )

    for machine in machines:
        if machine.recorded_downtime_seconds < 0:
            raise OperationalIntelligenceError(
                "Recorded downtime cannot be negative"
            )

        if machine.failure_count < 0:
            raise OperationalIntelligenceError(
                "Failure count cannot be negative"
            )

        if machine.failure_count > 0:
            if machine.mttr_seconds is None:
                raise OperationalIntelligenceError(
                    "Failed machines require MTTR"
                )

            if machine.mtbf_seconds is None:
                raise OperationalIntelligenceError(
                    "Failed machines require MTBF"
                )

    has_operational_concern = any(
        (
            machine.recorded_downtime_seconds > 0
            or machine.failure_count > 0
        )
        for machine in machines
    )

    if not has_operational_concern:
        no_concern_priorities = [
            MachineOperationalPriority(
                machine_id=machine.machine_id,
                machine_name=machine.machine_name,
                machine_code=machine.machine_code,
                priority_rank=None,
                downtime_rank=None,
                failure_rank=None,
                mttr_rank=None,
                mtbf_rank=None,
            )
            for machine in machines
        ]

        no_concern_priorities.sort(
            key=lambda item: (
                item.machine_code.casefold(),
                item.machine_id,
            )
        )

        return OperationalPrioritySummary(
            top_priority_machine_id=None,
            machines=tuple(no_concern_priorities),
        )

    downtime_ranks = _calculate_competition_ranks(
        {
            machine.machine_id: (
                machine.recorded_downtime_seconds
            )
            for machine in machines
        },
        higher_is_worse=True,
    )

    failure_ranks = _calculate_competition_ranks(
        {
            machine.machine_id: machine.failure_count
            for machine in machines
        },
        higher_is_worse=True,
    )

    failed_machines = [
        machine
        for machine in machines
        if machine.failure_count > 0
    ]

    mttr_ranks = _calculate_competition_ranks(
        {
            machine.machine_id: machine.mttr_seconds
            for machine in failed_machines
            if machine.mttr_seconds is not None
        },
        higher_is_worse=True,
    )

    mtbf_ranks = _calculate_competition_ranks(
        {
            machine.machine_id: machine.mtbf_seconds
            for machine in failed_machines
            if machine.mtbf_seconds is not None
        },
        higher_is_worse=False,
    )

    no_failure_reliability_rank = (
        len(failed_machines) + 1
    )

    aggregate_rank_values: dict[int, int] = {}

    for machine in machines:
        if machine.failure_count > 0:
            effective_mttr_rank = mttr_ranks[
                machine.machine_id
            ]

            effective_mtbf_rank = mtbf_ranks[
                machine.machine_id
            ]
        else:
            effective_mttr_rank = (
                no_failure_reliability_rank
            )

            effective_mtbf_rank = (
                no_failure_reliability_rank
            )

        aggregate_rank_values[machine.machine_id] = (
            downtime_ranks[machine.machine_id]
            + failure_ranks[machine.machine_id]
            + effective_mttr_rank
            + effective_mtbf_rank
        )

    priority_ranks = _calculate_competition_ranks(
        aggregate_rank_values,
        higher_is_worse=False,
    )

    priorities = [
        MachineOperationalPriority(
            machine_id=machine.machine_id,
            machine_name=machine.machine_name,
            machine_code=machine.machine_code,
            priority_rank=priority_ranks[
                machine.machine_id
            ],
            downtime_rank=downtime_ranks[
                machine.machine_id
            ],
            failure_rank=failure_ranks[
                machine.machine_id
            ],
            mttr_rank=(
                mttr_ranks[machine.machine_id]
                if machine.failure_count > 0
                else None
            ),
            mtbf_rank=(
                mtbf_ranks[machine.machine_id]
                if machine.failure_count > 0
                else None
            ),
        )
        for machine in machines
    ]

    impact_by_machine_id = {
        machine.machine_id: machine
        for machine in machines
    }

    priorities.sort(
        key=lambda item: (
            (
                item.priority_rank
                if item.priority_rank is not None
                else float("inf")
            ),
            -impact_by_machine_id[
                item.machine_id
            ].recorded_downtime_seconds,
            -impact_by_machine_id[
                item.machine_id
            ].failure_count,
            item.machine_code.casefold(),
            item.machine_id,
        )
    )

    return OperationalPrioritySummary(
        top_priority_machine_id=(
            priorities[0].machine_id
        ),
        machines=tuple(priorities),
    )


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