import pytest

from app.production.analytics import (
    ProductionAnalyticsError,
    RunOEEContribution,
    aggregate_oee,
)
from app.production.oee import OEEMetrics


def test_aggregate_oee_uses_underlying_production_facts() -> None:
    run_one_metrics = OEEMetrics(
        scheduled_time_seconds=3600,
        planned_downtime_seconds=0,
        planned_production_time_seconds=3600,
        unplanned_downtime_seconds=0,
        operating_time_seconds=3600,
        availability=1.0,
        performance=1000 / 3600,
        quality=0.9,
        oee=0.25,
    )

    run_two_metrics = OEEMetrics(
        scheduled_time_seconds=7200,
        planned_downtime_seconds=0,
        planned_production_time_seconds=7200,
        unplanned_downtime_seconds=3600,
        operating_time_seconds=3600,
        availability=0.5,
        performance=4000 / 3600,
        quality=0.5,
        oee=(0.5 * (4000 / 3600) * 0.5),
    )

    metrics = aggregate_oee(
        [
            RunOEEContribution(
                metrics=run_one_metrics,
                ideal_cycle_time_seconds=10.0,
                total_quantity=100,
                good_quantity=90,
            ),
            RunOEEContribution(
                metrics=run_two_metrics,
                ideal_cycle_time_seconds=20.0,
                total_quantity=200,
                good_quantity=100,
            ),
        ]
    )

    assert metrics.run_count == 2

    assert metrics.scheduled_time_seconds == 10800
    assert metrics.planned_downtime_seconds == 0
    assert metrics.planned_production_time_seconds == 10800

    assert metrics.unplanned_downtime_seconds == 3600
    assert metrics.operating_time_seconds == 7200

    assert metrics.total_quantity == 300
    assert metrics.good_quantity == 190

    assert metrics.availability == pytest.approx(
        7200 / 10800
    )

    assert metrics.performance == pytest.approx(
        5000 / 7200
    )

    assert metrics.quality == pytest.approx(
        190 / 300
    )

    assert metrics.oee == pytest.approx(
        (7200 / 10800)
        * (5000 / 7200)
        * (190 / 300)
    )

    naive_average_oee = (
        run_one_metrics.oee
        + run_two_metrics.oee
    ) / 2

    assert metrics.oee != pytest.approx(
        naive_average_oee
    )


def test_aggregate_oee_handles_different_ideal_cycle_times() -> None:
    first_metrics = OEEMetrics(
        scheduled_time_seconds=3600,
        planned_downtime_seconds=0,
        planned_production_time_seconds=3600,
        unplanned_downtime_seconds=0,
        operating_time_seconds=3600,
        availability=1.0,
        performance=0.5,
        quality=1.0,
        oee=0.5,
    )

    second_metrics = OEEMetrics(
        scheduled_time_seconds=3600,
        planned_downtime_seconds=0,
        planned_production_time_seconds=3600,
        unplanned_downtime_seconds=0,
        operating_time_seconds=3600,
        availability=1.0,
        performance=0.5,
        quality=1.0,
        oee=0.5,
    )

    metrics = aggregate_oee(
        [
            RunOEEContribution(
                metrics=first_metrics,
                ideal_cycle_time_seconds=10.0,
                total_quantity=180,
                good_quantity=180,
            ),
            RunOEEContribution(
                metrics=second_metrics,
                ideal_cycle_time_seconds=20.0,
                total_quantity=90,
                good_quantity=90,
            ),
        ]
    )

    ideal_production_time = (
        10.0 * 180
        + 20.0 * 90
    )

    assert metrics.performance == pytest.approx(
        ideal_production_time / 7200
    )

    assert metrics.total_quantity == 270
    assert metrics.good_quantity == 270
    assert metrics.quality == 1.0


def test_aggregate_oee_with_zero_production() -> None:
    metrics = aggregate_oee(
        [
            RunOEEContribution(
                metrics=OEEMetrics(
                    scheduled_time_seconds=3600,
                    planned_downtime_seconds=0,
                    planned_production_time_seconds=3600,
                    unplanned_downtime_seconds=0,
                    operating_time_seconds=3600,
                    availability=1.0,
                    performance=0.0,
                    quality=0.0,
                    oee=0.0,
                ),
                ideal_cycle_time_seconds=10.0,
                total_quantity=0,
                good_quantity=0,
            )
        ]
    )

    assert metrics.total_quantity == 0
    assert metrics.good_quantity == 0

    assert metrics.performance == 0.0
    assert metrics.quality == 0.0
    assert metrics.oee == 0.0


def test_aggregate_oee_with_zero_operating_time() -> None:
    metrics = aggregate_oee(
        [
            RunOEEContribution(
                metrics=OEEMetrics(
                    scheduled_time_seconds=3600,
                    planned_downtime_seconds=0,
                    planned_production_time_seconds=3600,
                    unplanned_downtime_seconds=3600,
                    operating_time_seconds=0,
                    availability=0.0,
                    performance=0.0,
                    quality=0.9,
                    oee=0.0,
                ),
                ideal_cycle_time_seconds=10.0,
                total_quantity=100,
                good_quantity=90,
            )
        ]
    )

    assert metrics.availability == 0.0
    assert metrics.performance == 0.0
    assert metrics.quality == pytest.approx(0.9)
    assert metrics.oee == 0.0


def test_aggregate_performance_is_not_capped() -> None:
    metrics = aggregate_oee(
        [
            RunOEEContribution(
                metrics=OEEMetrics(
                    scheduled_time_seconds=3600,
                    planned_downtime_seconds=0,
                    planned_production_time_seconds=3600,
                    unplanned_downtime_seconds=0,
                    operating_time_seconds=3600,
                    availability=1.0,
                    performance=4000 / 3600,
                    quality=1.0,
                    oee=4000 / 3600,
                ),
                ideal_cycle_time_seconds=10.0,
                total_quantity=400,
                good_quantity=400,
            )
        ]
    )

    assert metrics.performance == pytest.approx(
        4000 / 3600
    )

    assert metrics.performance > 1.0
    assert metrics.oee > 1.0


def test_aggregate_oee_requires_at_least_one_run() -> None:
    with pytest.raises(
        ProductionAnalyticsError,
        match=(
            "At least one completed production run "
            "is required"
        ),
    ):
        aggregate_oee([])


def test_aggregate_oee_requires_positive_planned_production_time() -> None:
    with pytest.raises(
        ProductionAnalyticsError,
        match=(
            "Aggregated planned production time "
            "must be greater than zero"
        ),
    ):
        aggregate_oee(
            [
                RunOEEContribution(
                    metrics=OEEMetrics(
                        scheduled_time_seconds=3600,
                        planned_downtime_seconds=3600,
                        planned_production_time_seconds=0,
                        unplanned_downtime_seconds=0,
                        operating_time_seconds=0,
                        availability=0.0,
                        performance=0.0,
                        quality=0.0,
                        oee=0.0,
                    ),
                    ideal_cycle_time_seconds=10.0,
                    total_quantity=0,
                    good_quantity=0,
                )
            ]
        )