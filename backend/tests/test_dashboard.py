from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from httpx import AsyncClient

from app.production.analytics import (
    AggregatedOEEMetrics,
)
from app.services import dashboard_service


def make_oee_metrics(
    *,
    oee: float,
    availability: float,
    run_count: int = 1,
) -> AggregatedOEEMetrics:
    return AggregatedOEEMetrics(
        run_count=run_count,
        scheduled_time_seconds=1000.0,
        planned_downtime_seconds=100.0,
        planned_production_time_seconds=900.0,
        unplanned_downtime_seconds=100.0,
        operating_time_seconds=800.0,
        total_quantity=100,
        good_quantity=95,
        availability=availability,
        performance=1.0,
        quality=1.0,
        oee=oee,
    )


@pytest.mark.parametrize(
    "role_name",
    [
        "admin",
        "manager",
        "technician",
        "operator",
    ],
)
async def test_dashboard_overview_available_to_all_roles(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
    role_name: str,
) -> None:
    response = await client.get(
        "/dashboard/overview",
        headers=auth_headers[role_name],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["period"] == {
        "start_at": None,
        "end_at": None,
    }

    assert data["kpis"] == {
        "overall_oee": None,
        "availability": None,
        "active_alert_count": 0,
        "fleet_mtbf_seconds": None,
    }

    assert data["production_lines"] == []

    assert data["machine_health"] == {
        "total_machines": 0,
        "healthy_count": 0,
        "attention_count": 0,
        "critical_count": 0,
    }

    assert data["recent_alerts"] == []
    assert data["needs_attention"] is None


async def test_dashboard_overview_requires_authentication(
    client: AsyncClient,
) -> None:
    response = await client.get(
        "/dashboard/overview"
    )

    assert response.status_code == 401


async def test_dashboard_overview_rejects_invalid_period(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    response = await client.get(
        (
            "/dashboard/overview"
            "?start_at=2026-08-29T12:00:00Z"
            "&end_at=2026-08-29T10:00:00Z"
        ),
        headers=auth_headers["operator"],
    )

    assert response.status_code == 422

    assert response.json()["detail"] == (
        "end_at must be later than start_at"
    )


async def test_dashboard_overview_uses_true_factory_aggregation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    production_lines = [
        SimpleNamespace(
            id=1,
            name="Assembly Line A",
            code="LINE-A",
        ),
        SimpleNamespace(
            id=2,
            name="Packaging Line B",
            code="LINE-B",
        ),
        SimpleNamespace(
            id=3,
            name="Assembly Line C",
            code="LINE-C",
        ),
    ]

    runs_by_line = {
        1: [
            SimpleNamespace(id=1),
        ],
        2: [
            SimpleNamespace(id=2),
        ],
        3: [],
    }

    async def fake_get_production_lines(
        db: object,
    ) -> list[SimpleNamespace]:
        return production_lines

    async def fake_get_completed_runs_for_line(
        db: object,
        production_line_id: int,
        start_at=None,
        end_at=None,
    ) -> list[SimpleNamespace]:
        return runs_by_line[
            production_line_id
        ]
    async def fake_calculate_factory_needs_attention(
        db: object,
        start_at=None,
        end_at=None,
    ):
        return None

    monkeypatch.setattr(
        dashboard_service,
        "calculate_factory_needs_attention",
        fake_calculate_factory_needs_attention,
    )

    async def fake_calculate_aggregated_oee_for_runs(
        db: object,
        production_runs: list[SimpleNamespace],
    ) -> AggregatedOEEMetrics:
        run_ids = {
            production_run.id
            for production_run in production_runs
        }

        if run_ids == {1}:
            return make_oee_metrics(
                oee=0.90,
                availability=0.95,
            )

        if run_ids == {2}:
            return make_oee_metrics(
                oee=0.50,
                availability=0.70,
            )

        if run_ids == {1, 2}:
            return make_oee_metrics(
                oee=0.62,
                availability=0.75,
                run_count=2,
            )

        raise AssertionError(
            f"Unexpected run ids: {run_ids}"
        )

    async def fake_get_active_alert_count(
        db: object,
    ) -> int:
        return 4

    async def fake_calculate_fleet_mtbf(
        db: object,
        start_at=None,
        end_at=None,
    ) -> float:
        return 18000.0

    async def fake_calculate_machine_health(
        db: object,
    ) -> dashboard_service.DashboardMachineHealthMetrics:
        return (
            dashboard_service.DashboardMachineHealthMetrics(
                total_machines=3,
                healthy_count=2,
                attention_count=1,
                critical_count=0,
            )
        )

    async def fake_get_recent_open_alerts(
        db: object,
        limit: int = 3,
    ) -> list[
        dashboard_service.DashboardRecentAlertMetrics
    ]:
        return []

    monkeypatch.setattr(
        dashboard_service,
        "get_production_lines",
        fake_get_production_lines,
    )

    monkeypatch.setattr(
        dashboard_service,
        "get_completed_runs_for_line",
        fake_get_completed_runs_for_line,
    )

    monkeypatch.setattr(
        dashboard_service,
        "calculate_aggregated_oee_for_runs",
        fake_calculate_aggregated_oee_for_runs,
    )

    monkeypatch.setattr(
        dashboard_service,
        "get_active_alert_count",
        fake_get_active_alert_count,
    )

    monkeypatch.setattr(
        dashboard_service,
        "calculate_fleet_mtbf",
        fake_calculate_fleet_mtbf,
    )

    monkeypatch.setattr(
        dashboard_service,
        "calculate_machine_health",
        fake_calculate_machine_health,
    )

    monkeypatch.setattr(
        dashboard_service,
        "get_recent_open_alerts",
        fake_get_recent_open_alerts,
    )

    result = (
        await dashboard_service.calculate_dashboard_overview(
            object(),
        )
    )

    assert result.overall_oee == 0.62
    assert result.availability == 0.75

    # A simple average would be 0.70.
    assert result.overall_oee != (
        0.90 + 0.50
    ) / 2

    assert result.active_alert_count == 4
    assert result.fleet_mtbf_seconds == 18000.0

    assert len(result.production_lines) == 3

    assert result.production_lines[0].oee == 0.90
    assert result.production_lines[1].oee == 0.50

    assert result.production_lines[2].oee is None

    assert (
        result.production_lines[2].availability
        is None
    )

    assert (
        result.machine_health.total_machines
        == 3
    )

    assert (
        result.machine_health.attention_count
        == 1
    )

    assert result.recent_alerts == []
    assert result.needs_attention is None



async def test_fleet_mtbf_uses_total_valid_exposure_over_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    machines = [
        SimpleNamespace(id=1),
        SimpleNamespace(id=2),
        SimpleNamespace(id=3),
    ]

    reliability_by_machine = {
        1: SimpleNamespace(
            operating_exposure_seconds=3600.0,
            failure_count=1,
        ),
        2: SimpleNamespace(
            operating_exposure_seconds=7200.0,
            failure_count=2,
        ),
        3: SimpleNamespace(
            operating_exposure_seconds=None,
            failure_count=10,
        ),
    }

    async def fake_get_machines(
        db: object,
    ) -> list[SimpleNamespace]:
        return machines

    async def fake_calculate_machine_reliability(
        db: object,
        machine_id: int,
        start_at=None,
        end_at=None,
    ) -> SimpleNamespace:
        return reliability_by_machine[
            machine_id
        ]

    monkeypatch.setattr(
        dashboard_service,
        "get_machines",
        fake_get_machines,
    )

    monkeypatch.setattr(
        dashboard_service,
        "calculate_machine_reliability",
        fake_calculate_machine_reliability,
    )

    result = (
        await dashboard_service.calculate_fleet_mtbf(
            object(),
        )
    )

    assert result == 3600.0


async def test_machine_health_uses_highest_open_alert_severity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    machines = [
        SimpleNamespace(id=1),
        SimpleNamespace(id=2),
        SimpleNamespace(id=3),
        SimpleNamespace(id=4),
    ]

    async def fake_get_machines(
        db: object,
    ) -> list[SimpleNamespace]:
        return machines

    class FakeResult:
        def all(self):
            return [
                (2, "medium"),
                (3, "future-severity"),
                (4, "medium"),
                (4, "critical"),
            ]

    class FakeDB:
        async def execute(
            self,
            statement: object,
        ) -> FakeResult:
            return FakeResult()

    monkeypatch.setattr(
        dashboard_service,
        "get_machines",
        fake_get_machines,
    )

    result = (
        await dashboard_service.calculate_machine_health(
            FakeDB(),
        )
    )

    assert result.total_machines == 4

    assert result.healthy_count == 1
    assert result.attention_count == 2
    assert result.critical_count == 1


async def test_recent_alerts_include_machine_context(
) -> None:
    created_at = datetime(
        2026,
        8,
        29,
        10,
        30,
        tzinfo=timezone.utc,
    )

    alert = SimpleNamespace(
        id=17,
        severity="critical",
        title="Motor temperature",
        message=(
            "Motor temperature exceeded threshold"
        ),
        created_at=created_at,
    )

    machine = SimpleNamespace(
        id=8,
        name="Press M-101",
        code="M-101",
    )

    class FakeResult:
        def all(self):
            return [
                (alert, machine),
            ]

    class FakeDB:
        async def execute(
            self,
            statement: object,
        ) -> FakeResult:
            return FakeResult()

    result = (
        await dashboard_service.get_recent_open_alerts(
            FakeDB(),
            limit=3,
        )
    )

    assert len(result) == 1

    recent_alert = result[0]

    assert recent_alert.id == 17
    assert recent_alert.machine_id == 8
    assert recent_alert.machine_name == "Press M-101"
    assert recent_alert.machine_code == "M-101"

    assert recent_alert.severity == "critical"

    assert recent_alert.title == (
        "Motor temperature"
    )

    assert recent_alert.message == (
        "Motor temperature exceeded threshold"
    )

    assert recent_alert.created_at == created_at


async def test_factory_needs_attention_recomputes_priority_across_lines(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    production_lines = [
        SimpleNamespace(
            id=1,
            name="Assembly Line A",
            code="LINE-A",
        ),
        SimpleNamespace(
            id=2,
            name="Packaging Line B",
            code="LINE-B",
        ),
    ]

    runs_by_line = {
        1: [
            SimpleNamespace(id=101),
        ],
        2: [
            SimpleNamespace(id=201),
        ],
    }

    line_a_machine = SimpleNamespace(
        machine_id=11,
        machine_name="Press M-101",
        machine_code="M-101",
        recorded_downtime_event_count=1,
        recorded_downtime_seconds=1000.0,
        recorded_downtime_share=1.0,
        failure_count=0,
        mttr_seconds=None,
        operating_exposure_seconds=7200.0,
        mtbf_seconds=None,
    )

    line_b_machine = SimpleNamespace(
        machine_id=22,
        machine_name="Conveyor M-204",
        machine_code="M-204",
        recorded_downtime_event_count=3,
        recorded_downtime_seconds=500.0,
        recorded_downtime_share=1.0,
        failure_count=3,
        mttr_seconds=1200.0,
        operating_exposure_seconds=9000.0,
        mtbf_seconds=3000.0,
    )

    async def fake_get_production_lines(
        db: object,
    ) -> list[SimpleNamespace]:
        return production_lines

    async def fake_get_completed_runs_for_line(
        db: object,
        production_line_id: int,
        start_at=None,
        end_at=None,
    ) -> list[SimpleNamespace]:
        return runs_by_line[
            production_line_id
        ]

    async def fake_operational_intelligence(
        db: object,
        production_line_id: int,
        start_at=None,
        end_at=None,
    ) -> SimpleNamespace:
        if production_line_id == 1:
            return SimpleNamespace(
                operational_impact=SimpleNamespace(
                    machines=(
                        line_a_machine,
                    ),
                ),
                downtime_reasons=(
                    SimpleNamespace(
                        machine_id=11,
                        dominant_duration_reason=(
                            "Motor Overheating"
                        ),
                        by_reason=(
                            SimpleNamespace(
                                reason=(
                                    "Motor Overheating"
                                ),
                                percentage=1.0,
                            ),
                        ),
                    ),
                ),
            )

        return SimpleNamespace(
            operational_impact=SimpleNamespace(
                machines=(
                    line_b_machine,
                ),
            ),
            downtime_reasons=(
                SimpleNamespace(
                    machine_id=22,
                    dominant_duration_reason=(
                        "Bearing Wear"
                    ),
                    by_reason=(
                        SimpleNamespace(
                            reason="Bearing Wear",
                            percentage=0.75,
                        ),
                        SimpleNamespace(
                            reason="Other",
                            percentage=0.25,
                        ),
                    ),
                ),
            ),
        )

    monkeypatch.setattr(
        dashboard_service,
        "get_production_lines",
        fake_get_production_lines,
    )

    monkeypatch.setattr(
        dashboard_service,
        "get_completed_runs_for_line",
        fake_get_completed_runs_for_line,
    )

    monkeypatch.setattr(
        dashboard_service,
        "calculate_production_line_operational_intelligence",
        fake_operational_intelligence,
    )

    result = (
        await dashboard_service
        .calculate_factory_needs_attention(
            object(),
        )
    )

    assert result is not None

    # Each line contains only one machine,
    # so each would be local rank #1.
    # FactoryPulse must recompute one
    # cross-line ranking instead.
    assert result.machine_id == 22
    assert result.machine_name == (
        "Conveyor M-204"
    )

    assert result.production_line_id == 2
    assert result.production_line_name == (
        "Packaging Line B"
    )

    assert result.priority_rank == 1

    assert (
        result.recorded_downtime_seconds
        == 500.0
    )

    assert result.failure_count == 3
    assert result.mttr_seconds == 1200.0
    assert result.mtbf_seconds == 3000.0

    assert result.dominant_reason == (
        "Bearing Wear"
    )

    assert (
        result.dominant_reason_percentage
        == 0.75
    )

    