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

    result = (
        await dashboard_service.calculate_dashboard_overview(
            object(),
        )
    )

    assert result.overall_oee == 0.62
    assert result.availability == 0.75

    # A simple average would be 0.70.
    # FactoryPulse must use aggregated run data.
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