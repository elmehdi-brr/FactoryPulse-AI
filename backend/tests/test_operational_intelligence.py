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
    MachineOperationalImpact,
    calculate_operational_priority,
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


def operational_impact(
    *,
    machine_id: int,
    machine_name: str,
    machine_code: str,
    downtime_seconds: float,
    failure_count: int,
    mttr_seconds: float | None,
    mtbf_seconds: float | None,
) -> MachineOperationalImpact:
    return MachineOperationalImpact(
        machine_id=machine_id,
        machine_name=machine_name,
        machine_code=machine_code,
        recorded_downtime_event_count=failure_count,
        recorded_downtime_seconds=downtime_seconds,
        recorded_downtime_share=None,
        failure_count=failure_count,
        mttr_seconds=mttr_seconds,
        operating_exposure_seconds=None,
        mtbf_seconds=mtbf_seconds,
    )


def test_operational_priority_ranks_machine_evidence() -> None:
    result = calculate_operational_priority(
        [
            operational_impact(
                machine_id=1,
                machine_name="Machine A",
                machine_code="M-A",
                downtime_seconds=7200,
                failure_count=3,
                mttr_seconds=1800,
                mtbf_seconds=7200,
            ),
            operational_impact(
                machine_id=2,
                machine_name="Machine B",
                machine_code="M-B",
                downtime_seconds=3600,
                failure_count=1,
                mttr_seconds=3600,
                mtbf_seconds=18_000,
            ),
            operational_impact(
                machine_id=3,
                machine_name="Machine C",
                machine_code="M-C",
                downtime_seconds=0,
                failure_count=0,
                mttr_seconds=None,
                mtbf_seconds=None,
            ),
        ]
    )

    assert result.top_priority_machine_id == 1

    assert [
        item.machine_id
        for item in result.machines
    ] == [1, 2, 3]

    machine_a = result.machines[0]
    machine_b = result.machines[1]
    machine_c = result.machines[2]

    assert machine_a.priority_rank == 1
    assert machine_a.downtime_rank == 1
    assert machine_a.failure_rank == 1
    assert machine_a.mttr_rank == 2
    assert machine_a.mtbf_rank == 1

    assert machine_b.priority_rank == 2
    assert machine_b.downtime_rank == 2
    assert machine_b.failure_rank == 2
    assert machine_b.mttr_rank == 1
    assert machine_b.mtbf_rank == 2

    assert machine_c.priority_rank == 3
    assert machine_c.downtime_rank == 3
    assert machine_c.failure_rank == 3

    assert machine_c.mttr_rank is None
    assert machine_c.mtbf_rank is None


def test_operational_priority_uses_competition_ranking_for_ties() -> None:
    result = calculate_operational_priority(
        [
            operational_impact(
                machine_id=1,
                machine_name="Machine A",
                machine_code="M-A",
                downtime_seconds=3600,
                failure_count=1,
                mttr_seconds=1800,
                mtbf_seconds=10_000,
            ),
            operational_impact(
                machine_id=2,
                machine_name="Machine B",
                machine_code="M-B",
                downtime_seconds=3600,
                failure_count=1,
                mttr_seconds=1800,
                mtbf_seconds=10_000,
            ),
            operational_impact(
                machine_id=3,
                machine_name="Machine C",
                machine_code="M-C",
                downtime_seconds=1800,
                failure_count=1,
                mttr_seconds=900,
                mtbf_seconds=20_000,
            ),
        ]
    )

    machine_a = next(
        item
        for item in result.machines
        if item.machine_id == 1
    )

    machine_b = next(
        item
        for item in result.machines
        if item.machine_id == 2
    )

    machine_c = next(
        item
        for item in result.machines
        if item.machine_id == 3
    )

    assert machine_a.downtime_rank == 1
    assert machine_b.downtime_rank == 1
    assert machine_c.downtime_rank == 3

    assert machine_a.failure_rank == 1
    assert machine_b.failure_rank == 1
    assert machine_c.failure_rank == 1

    assert machine_a.priority_rank == 1
    assert machine_b.priority_rank == 1
    assert machine_c.priority_rank == 3


def test_operational_priority_does_not_penalize_zero_failure_mtbf() -> None:
    result = calculate_operational_priority(
        [
            operational_impact(
                machine_id=1,
                machine_name="Failed Machine",
                machine_code="FAILED",
                downtime_seconds=1800,
                failure_count=1,
                mttr_seconds=1800,
                mtbf_seconds=10_000,
            ),
            operational_impact(
                machine_id=2,
                machine_name="Healthy Machine",
                machine_code="HEALTHY",
                downtime_seconds=0,
                failure_count=0,
                mttr_seconds=None,
                mtbf_seconds=None,
            ),
        ]
    )

    assert result.top_priority_machine_id == 1

    failed_machine = result.machines[0]
    healthy_machine = result.machines[1]

    assert failed_machine.priority_rank == 1
    assert healthy_machine.priority_rank == 2

    assert healthy_machine.mttr_rank is None
    assert healthy_machine.mtbf_rank is None


def test_operational_priority_has_no_priority_without_concern() -> None:
    result = calculate_operational_priority(
        [
            operational_impact(
                machine_id=1,
                machine_name="Machine A",
                machine_code="M-A",
                downtime_seconds=0,
                failure_count=0,
                mttr_seconds=None,
                mtbf_seconds=None,
            ),
            operational_impact(
                machine_id=2,
                machine_name="Machine B",
                machine_code="M-B",
                downtime_seconds=0,
                failure_count=0,
                mttr_seconds=None,
                mtbf_seconds=None,
            ),
        ]
    )

    assert result.top_priority_machine_id is None

    assert all(
        machine.priority_rank is None
        for machine in result.machines
    )

    assert all(
        machine.downtime_rank is None
        for machine in result.machines
    )

    assert all(
        machine.failure_rank is None
        for machine in result.machines
    )


def test_operational_priority_rejects_incomplete_failed_machine_metrics() -> None:
    with pytest.raises(
        OperationalIntelligenceError,
        match="Failed machines require MTTR",
    ):
        calculate_operational_priority(
            [
                operational_impact(
                    machine_id=1,
                    machine_name="Machine A",
                    machine_code="M-A",
                    downtime_seconds=3600,
                    failure_count=1,
                    mttr_seconds=None,
                    mtbf_seconds=10_000,
                )
            ]
        )