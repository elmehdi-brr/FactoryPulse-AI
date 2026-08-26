from dataclasses import dataclass
from typing import Sequence

from app.production.oee import OEEMetrics


class ProductionAnalyticsError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RunOEEContribution:
    metrics: OEEMetrics

    ideal_cycle_time_seconds: float
    total_quantity: int
    good_quantity: int


@dataclass(frozen=True, slots=True)
class AggregatedOEEMetrics:
    run_count: int

    scheduled_time_seconds: float

    planned_downtime_seconds: float
    planned_production_time_seconds: float

    unplanned_downtime_seconds: float
    operating_time_seconds: float

    total_quantity: int
    good_quantity: int

    availability: float
    performance: float
    quality: float
    oee: float


def aggregate_oee(
    contributions: Sequence[RunOEEContribution],
) -> AggregatedOEEMetrics:
    if not contributions:
        raise ProductionAnalyticsError(
            "At least one completed production run is required"
        )

    scheduled_time_seconds = sum(
        contribution.metrics.scheduled_time_seconds
        for contribution in contributions
    )

    planned_downtime_seconds = sum(
        contribution.metrics.planned_downtime_seconds
        for contribution in contributions
    )

    planned_production_time_seconds = sum(
        contribution.metrics.planned_production_time_seconds
        for contribution in contributions
    )

    unplanned_downtime_seconds = sum(
        contribution.metrics.unplanned_downtime_seconds
        for contribution in contributions
    )

    operating_time_seconds = sum(
        contribution.metrics.operating_time_seconds
        for contribution in contributions
    )

    total_quantity = sum(
        contribution.total_quantity
        for contribution in contributions
    )

    good_quantity = sum(
        contribution.good_quantity
        for contribution in contributions
    )

    ideal_production_time_seconds = sum(
        contribution.ideal_cycle_time_seconds
        * contribution.total_quantity
        for contribution in contributions
    )

    if planned_production_time_seconds <= 0:
        raise ProductionAnalyticsError(
            "Aggregated planned production time must be greater than zero"
        )

    availability = (
        operating_time_seconds
        / planned_production_time_seconds
    )

    if operating_time_seconds == 0:
        performance = 0.0
    else:
        performance = (
            ideal_production_time_seconds
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

    return AggregatedOEEMetrics(
        run_count=len(contributions),
        scheduled_time_seconds=scheduled_time_seconds,
        planned_downtime_seconds=planned_downtime_seconds,
        planned_production_time_seconds=(
            planned_production_time_seconds
        ),
        unplanned_downtime_seconds=(
            unplanned_downtime_seconds
        ),
        operating_time_seconds=operating_time_seconds,
        total_quantity=total_quantity,
        good_quantity=good_quantity,
        availability=availability,
        performance=performance,
        quality=quality,
        oee=oee,
    )