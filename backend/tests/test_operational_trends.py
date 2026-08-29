import pytest

from app.production.operational_trends import (
    MachinePeriodSnapshot,
    OperationalPeriodSnapshot,
    calculate_metric_trend,
    calculate_operational_trends,
)


def machine(
    *,
    machine_id: int,
    code: str,
    downtime: float,
    failures: int,
    mttr: float | None,
    mtbf: float | None,
) -> MachinePeriodSnapshot:
    return MachinePeriodSnapshot(
        machine_id=machine_id,
        machine_name=f"Machine {code}",
        machine_code=code,
        recorded_downtime_seconds=downtime,
        failure_count=failures,
        mttr_seconds=mttr,
        mtbf_seconds=mtbf,
    )


def test_metric_trend_higher_is_better() -> None:
    result = calculate_metric_trend(
        0.80,
        0.70,
        higher_is_better=True,
    )

    assert result.current_value == pytest.approx(0.80)
    assert result.previous_value == pytest.approx(0.70)
    assert result.delta == pytest.approx(0.10)
    assert result.direction == "improved"


def test_metric_trend_lower_is_better() -> None:
    result = calculate_metric_trend(
        8 * 3600,
        12 * 3600,
        higher_is_better=False,
    )

    assert result.delta == pytest.approx(-4 * 3600)
    assert result.direction == "improved"


def test_metric_trend_handles_equal_values() -> None:
    result = calculate_metric_trend(
        5,
        5,
        higher_is_better=False,
    )

    assert result.delta == 0.0
    assert result.direction == "unchanged"


def test_metric_trend_handles_missing_value() -> None:
    result = calculate_metric_trend(
        None,
        7200,
        higher_is_better=True,
    )

    assert result.delta is None
    assert result.direction == "not_comparable"


def test_operational_trends_compare_line_and_machine_metrics() -> None:
    previous = OperationalPeriodSnapshot(
        oee=0.70,
        availability=0.75,
        performance=0.95,
        quality=0.98,
        recorded_downtime_seconds=12 * 3600,
        total_failure_count=5,
        machines=(
            machine(
                machine_id=1,
                code="M-A",
                downtime=8 * 3600,
                failures=3,
                mttr=3600,
                mtbf=7200,
            ),
            machine(
                machine_id=2,
                code="M-B",
                downtime=4 * 3600,
                failures=2,
                mttr=1800,
                mtbf=12_000,
            ),
        ),
    )

    current = OperationalPeriodSnapshot(
        oee=0.80,
        availability=0.85,
        performance=0.97,
        quality=0.99,
        recorded_downtime_seconds=8 * 3600,
        total_failure_count=3,
        machines=(
            machine(
                machine_id=1,
                code="M-A",
                downtime=5 * 3600,
                failures=2,
                mttr=2400,
                mtbf=10_000,
            ),
            machine(
                machine_id=2,
                code="M-B",
                downtime=3 * 3600,
                failures=1,
                mttr=1200,
                mtbf=18_000,
            ),
        ),
    )

    result = calculate_operational_trends(
        current,
        previous,
    )

    assert result.oee.direction == "improved"
    assert result.availability.direction == "improved"
    assert result.performance.direction == "improved"
    assert result.quality.direction == "improved"

    assert result.recorded_downtime.direction == "improved"
    assert result.recorded_downtime.delta == pytest.approx(
        -4 * 3600
    )

    assert result.total_failure_count.direction == "improved"
    assert result.total_failure_count.delta == pytest.approx(-2)

    machine_a = result.machines[0]

    assert machine_a.machine_id == 1

    assert (
        machine_a.recorded_downtime.direction
        == "improved"
    )

    assert machine_a.failure_count.direction == "improved"
    assert machine_a.mttr.direction == "improved"
    assert machine_a.mtbf.direction == "improved"


def test_operational_trends_do_not_penalize_no_failure_mtbf() -> None:
    previous = OperationalPeriodSnapshot(
        oee=0.70,
        availability=0.80,
        performance=0.90,
        quality=0.98,
        recorded_downtime_seconds=3600,
        total_failure_count=1,
        machines=(
            machine(
                machine_id=1,
                code="M-A",
                downtime=3600,
                failures=1,
                mttr=3600,
                mtbf=10_000,
            ),
        ),
    )

    current = OperationalPeriodSnapshot(
        oee=0.80,
        availability=0.90,
        performance=0.95,
        quality=0.99,
        recorded_downtime_seconds=0,
        total_failure_count=0,
        machines=(
            machine(
                machine_id=1,
                code="M-A",
                downtime=0,
                failures=0,
                mttr=None,
                mtbf=None,
            ),
        ),
    )

    result = calculate_operational_trends(
        current,
        previous,
    )

    machine_a = result.machines[0]

    assert machine_a.failure_count.direction == "improved"

    assert machine_a.mttr.delta is None
    assert machine_a.mttr.direction == "not_comparable"

    assert machine_a.mtbf.delta is None
    assert machine_a.mtbf.direction == "not_comparable"