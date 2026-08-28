from datetime import datetime, timezone

import pytest

from app.production.downtime_analytics import (
    DowntimeAnalyticsEvent,
    calculate_downtime_analytics,
)
from app.production.operational_intelligence import (
    MachineReliabilitySnapshot,
    OperationalIntelligenceError,
    calculate_operational_downtime_impact,
)


def dt(hour: int, minute: int = 0) -> datetime:
    return datetime(
        2026,
        8,
        20,
        hour,
        minute,
        tzinfo=timezone.utc,
    )


def test_calculates_machine_downtime_impact() -> None:
    downtime_metrics = calculate_downtime_analytics(
        [
            DowntimeAnalyticsEvent(
                reason="Motor Failure",
                category="unplanned",
                started_at=dt(8),
                ended_at=dt(9),
                machine_id=1,
            ),
            DowntimeAnalyticsEvent(
                reason="Bearing Failure",
                category="unplanned",
                started_at=dt(10),
                ended_at=dt(11),
                machine_id=1,
            ),
            DowntimeAnalyticsEvent(
                reason="Sensor Failure",
                category="unplanned",
                started_at=dt(11),
                ended_at=dt(11, 30),
                machine_id=2,
            ),
            DowntimeAnalyticsEvent(
                reason="Changeover",
                category="planned",
                started_at=dt(12),
                ended_at=dt(12, 30),
                machine_id=None,
            ),
        ]
    )

    result = calculate_operational_downtime_impact(
        downtime_metrics,
        [
            MachineReliabilitySnapshot(
                machine_id=1,
                machine_name="Machine A",
                machine_code="M-A",
                failure_count=2,
                mttr_seconds=3600,
                operating_exposure_seconds=20_000,
                mtbf_seconds=10_000,
            ),
            MachineReliabilitySnapshot(
                machine_id=2,
                machine_name="Machine B",
                machine_code="M-B",
                failure_count=1,
                mttr_seconds=1800,
                operating_exposure_seconds=30_000,
                mtbf_seconds=30_000,
            ),
        ],
    )

    assert result.recorded_downtime_seconds == pytest.approx(
        3 * 3600
    )

    assert (
        result.machine_attributed_recorded_downtime_seconds
        == pytest.approx(2.5 * 3600)
    )

    assert (
        result.unattributed_recorded_downtime_seconds
        == pytest.approx(0.5 * 3600)
    )

    assert result.machine_attributed_share == pytest.approx(
        5 / 6
    )

    assert result.unattributed_share == pytest.approx(
        1 / 6
    )

    assert result.top_downtime_machine_id == 1

    assert len(result.machines) == 2

    machine_a = result.machines[0]
    machine_b = result.machines[1]

    assert machine_a.machine_id == 1
    assert machine_a.recorded_downtime_event_count == 2
    assert machine_a.recorded_downtime_seconds == pytest.approx(
        2 * 3600
    )
    assert machine_a.recorded_downtime_share == pytest.approx(
        2 / 3
    )
    assert machine_a.failure_count == 2
    assert machine_a.mttr_seconds == pytest.approx(3600)
    assert machine_a.mtbf_seconds == pytest.approx(10_000)

    assert machine_b.machine_id == 2
    assert machine_b.recorded_downtime_seconds == pytest.approx(
        0.5 * 3600
    )
    assert machine_b.recorded_downtime_share == pytest.approx(
        1 / 6
    )


def test_machine_without_downtime_is_still_in_report() -> None:
    downtime_metrics = calculate_downtime_analytics(
        [
            DowntimeAnalyticsEvent(
                reason="Machine A Failure",
                category="unplanned",
                started_at=dt(8),
                ended_at=dt(9),
                machine_id=1,
            )
        ]
    )

    result = calculate_operational_downtime_impact(
        downtime_metrics,
        [
            MachineReliabilitySnapshot(
                machine_id=1,
                machine_name="Machine A",
                machine_code="M-A",
                failure_count=1,
                mttr_seconds=3600,
                operating_exposure_seconds=10_000,
                mtbf_seconds=10_000,
            ),
            MachineReliabilitySnapshot(
                machine_id=2,
                machine_name="Machine B",
                machine_code="M-B",
                failure_count=0,
                mttr_seconds=None,
                operating_exposure_seconds=14_000,
                mtbf_seconds=None,
            ),
        ],
    )

    machine_b = result.machines[1]

    assert machine_b.machine_id == 2
    assert machine_b.recorded_downtime_event_count == 0
    assert machine_b.recorded_downtime_seconds == 0.0
    assert machine_b.recorded_downtime_share == 0.0


def test_no_downtime_has_nullable_shares() -> None:
    downtime_metrics = calculate_downtime_analytics([])

    result = calculate_operational_downtime_impact(
        downtime_metrics,
        [
            MachineReliabilitySnapshot(
                machine_id=1,
                machine_name="Machine A",
                machine_code="M-A",
                failure_count=0,
                mttr_seconds=None,
                operating_exposure_seconds=14_000,
                mtbf_seconds=None,
            )
        ],
    )

    assert result.recorded_downtime_seconds == 0.0
    assert result.machine_attributed_share is None
    assert result.unattributed_share is None
    assert result.top_downtime_machine_id is None

    assert (
        result.machines[0].recorded_downtime_share
        is None
    )


def test_rejects_duplicate_machine_ids() -> None:
    downtime_metrics = calculate_downtime_analytics([])

    with pytest.raises(
        OperationalIntelligenceError,
        match="Machine IDs must be unique",
    ):
        calculate_operational_downtime_impact(
            downtime_metrics,
            [
                MachineReliabilitySnapshot(
                    machine_id=1,
                    machine_name="Machine A",
                    machine_code="M-A",
                    failure_count=0,
                    mttr_seconds=None,
                    operating_exposure_seconds=None,
                    mtbf_seconds=None,
                ),
                MachineReliabilitySnapshot(
                    machine_id=1,
                    machine_name="Duplicate",
                    machine_code="M-B",
                    failure_count=0,
                    mttr_seconds=None,
                    operating_exposure_seconds=None,
                    mtbf_seconds=None,
                ),
            ],
        )