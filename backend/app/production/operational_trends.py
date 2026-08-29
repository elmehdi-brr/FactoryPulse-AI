from dataclasses import dataclass
from typing import Literal, Sequence


TrendDirection = Literal[
    "improved",
    "worsened",
    "unchanged",
    "not_comparable",
]


class OperationalTrendError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class OperationalMetricTrend:
    current_value: float | int | None
    previous_value: float | int | None

    delta: float | None
    direction: TrendDirection


@dataclass(frozen=True, slots=True)
class MachinePeriodSnapshot:
    machine_id: int
    machine_name: str
    machine_code: str

    recorded_downtime_seconds: float
    failure_count: int

    mttr_seconds: float | None
    mtbf_seconds: float | None


@dataclass(frozen=True, slots=True)
class OperationalPeriodSnapshot:
    oee: float
    availability: float
    performance: float
    quality: float

    recorded_downtime_seconds: float
    total_failure_count: int

    machines: tuple[
        MachinePeriodSnapshot,
        ...,
    ]


@dataclass(frozen=True, slots=True)
class MachineOperationalTrend:
    machine_id: int
    machine_name: str
    machine_code: str

    recorded_downtime: OperationalMetricTrend
    failure_count: OperationalMetricTrend
    mttr: OperationalMetricTrend
    mtbf: OperationalMetricTrend


@dataclass(frozen=True, slots=True)
class OperationalTrendSummary:
    oee: OperationalMetricTrend
    availability: OperationalMetricTrend
    performance: OperationalMetricTrend
    quality: OperationalMetricTrend

    recorded_downtime: OperationalMetricTrend
    total_failure_count: OperationalMetricTrend

    machines: tuple[
        MachineOperationalTrend,
        ...,
    ]


def calculate_metric_trend(
    current_value: float | int | None,
    previous_value: float | int | None,
    *,
    higher_is_better: bool,
) -> OperationalMetricTrend:
    if (
        current_value is None
        or previous_value is None
    ):
        return OperationalMetricTrend(
            current_value=current_value,
            previous_value=previous_value,
            delta=None,
            direction="not_comparable",
        )

    delta = float(current_value - previous_value)

    if delta == 0:
        direction: TrendDirection = "unchanged"

    elif higher_is_better:
        direction = (
            "improved"
            if delta > 0
            else "worsened"
        )

    else:
        direction = (
            "improved"
            if delta < 0
            else "worsened"
        )

    return OperationalMetricTrend(
        current_value=current_value,
        previous_value=previous_value,
        delta=delta,
        direction=direction,
    )


def calculate_operational_trends(
    current: OperationalPeriodSnapshot,
    previous: OperationalPeriodSnapshot,
) -> OperationalTrendSummary:
    current_machine_ids = [
        machine.machine_id
        for machine in current.machines
    ]

    previous_machine_ids = [
        machine.machine_id
        for machine in previous.machines
    ]

    if len(current_machine_ids) != len(
        set(current_machine_ids)
    ):
        raise OperationalTrendError(
            "Current-period machine IDs must be unique"
        )

    if len(previous_machine_ids) != len(
        set(previous_machine_ids)
    ):
        raise OperationalTrendError(
            "Previous-period machine IDs must be unique"
        )

    current_by_machine = {
        machine.machine_id: machine
        for machine in current.machines
    }

    previous_by_machine = {
        machine.machine_id: machine
        for machine in previous.machines
    }

    all_machine_ids = (
        set(current_by_machine)
        | set(previous_by_machine)
    )

    machine_trends: list[
        MachineOperationalTrend
    ] = []

    for machine_id in all_machine_ids:
        current_machine = current_by_machine.get(
            machine_id
        )

        previous_machine = previous_by_machine.get(
            machine_id
        )

        reference_machine = (
            current_machine
            if current_machine is not None
            else previous_machine
        )

        if reference_machine is None:
            raise OperationalTrendError(
                "Machine comparison state is invalid"
            )

        current_downtime = (
            current_machine.recorded_downtime_seconds
            if current_machine is not None
            else None
        )

        previous_downtime = (
            previous_machine.recorded_downtime_seconds
            if previous_machine is not None
            else None
        )

        current_failures = (
            current_machine.failure_count
            if current_machine is not None
            else None
        )

        previous_failures = (
            previous_machine.failure_count
            if previous_machine is not None
            else None
        )

        current_mttr = (
            current_machine.mttr_seconds
            if current_machine is not None
            else None
        )

        previous_mttr = (
            previous_machine.mttr_seconds
            if previous_machine is not None
            else None
        )

        current_mtbf = (
            current_machine.mtbf_seconds
            if current_machine is not None
            else None
        )

        previous_mtbf = (
            previous_machine.mtbf_seconds
            if previous_machine is not None
            else None
        )

        machine_trends.append(
            MachineOperationalTrend(
                machine_id=reference_machine.machine_id,
                machine_name=(
                    reference_machine.machine_name
                ),
                machine_code=(
                    reference_machine.machine_code
                ),
                recorded_downtime=calculate_metric_trend(
                    current_downtime,
                    previous_downtime,
                    higher_is_better=False,
                ),
                failure_count=calculate_metric_trend(
                    current_failures,
                    previous_failures,
                    higher_is_better=False,
                ),
                mttr=calculate_metric_trend(
                    current_mttr,
                    previous_mttr,
                    higher_is_better=False,
                ),
                mtbf=calculate_metric_trend(
                    current_mtbf,
                    previous_mtbf,
                    higher_is_better=True,
                ),
            )
        )

    machine_trends.sort(
        key=lambda item: (
            item.machine_code.casefold(),
            item.machine_id,
        )
    )

    return OperationalTrendSummary(
        oee=calculate_metric_trend(
            current.oee,
            previous.oee,
            higher_is_better=True,
        ),
        availability=calculate_metric_trend(
            current.availability,
            previous.availability,
            higher_is_better=True,
        ),
        performance=calculate_metric_trend(
            current.performance,
            previous.performance,
            higher_is_better=True,
        ),
        quality=calculate_metric_trend(
            current.quality,
            previous.quality,
            higher_is_better=True,
        ),
        recorded_downtime=calculate_metric_trend(
            current.recorded_downtime_seconds,
            previous.recorded_downtime_seconds,
            higher_is_better=False,
        ),
        total_failure_count=calculate_metric_trend(
            current.total_failure_count,
            previous.total_failure_count,
            higher_is_better=False,
        ),
        machines=tuple(machine_trends),
    )