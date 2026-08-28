import pytest
from httpx import AsyncClient
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.db.session import AsyncSessionLocal
from app.models.production_run import ProductionRun
from app.models.downtime_event import DowntimeEvent
from app.services.machine_reliability_service import (
    MachineReliabilityServiceError,
    calculate_machine_reliability,
)
from app.services.operational_intelligence_service import (
    OperationalIntelligenceServiceError,
    calculate_production_line_operational_intelligence,
)


async def create_production_test_hierarchy(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> dict[str, int]:
    organization_response = await client.post(
        "/organizations",
        headers=admin_headers,
        json={
            "name": "Production Test Organization",
            "code": "PROD-ORG",
            "description": "Production and OEE tests",
        },
    )

    assert organization_response.status_code == 201
    organization_id = organization_response.json()["id"]

    site_response = await client.post(
        "/sites",
        headers=admin_headers,
        json={
            "organization_id": organization_id,
            "name": "Production Test Site",
            "code": "PROD-SITE",
            "location": "Test",
            "description": "Production test site",
        },
    )

    assert site_response.status_code == 201
    site_id = site_response.json()["id"]

    area_response = await client.post(
        "/areas",
        headers=admin_headers,
        json={
            "site_id": site_id,
            "name": "Production Area",
            "code": "PROD-AREA",
            "description": "Production test area",
        },
    )

    assert area_response.status_code == 201
    area_id = area_response.json()["id"]

    line_response = await client.post(
        "/production-lines",
        headers=admin_headers,
        json={
            "area_id": area_id,
            "name": "Assembly Line A",
            "code": "LINE-A",
            "description": "Primary assembly line",
        },
    )

    assert line_response.status_code == 201
    production_line_id = line_response.json()["id"]

    machine_response = await client.post(
        "/machines",
        headers=admin_headers,
        json={
            "area_id": area_id,
            "production_line_id": production_line_id,
            "name": "Assembly Machine A",
            "code": "MACHINE-A",
            "location": "Assembly Line A",
            "status": "active",
        },
    )

    assert machine_response.status_code == 201
    machine_id = machine_response.json()["id"]

    return {
        "organization_id": organization_id,
        "site_id": site_id,
        "area_id": area_id,
        "production_line_id": production_line_id,
        "machine_id": machine_id,
    }


async def create_test_production_run(
    client: AsyncClient,
    admin_headers: dict[str, str],
    production_line_id: int,
) -> dict:
    response = await client.post(
        "/production-runs",
        headers=admin_headers,
        json={
            "production_line_id": production_line_id,
            "started_at": "2026-08-25T08:00:00Z",
            "ended_at": None,
            "status": "running",
            "target_quantity": 1000,
            "total_quantity": 0,
            "good_quantity": 0,
            "reject_quantity": 0,
            "ideal_cycle_time_seconds": 5.0,
        },
    )

    assert response.status_code == 201

    return response.json()


async def test_create_production_run(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    response = await client.post(
        "/production-runs",
        headers=auth_headers["admin"],
        json={
            "production_line_id": hierarchy["production_line_id"],
            "started_at": "2026-08-25T08:00:00Z",
            "status": "running",
            "target_quantity": 1000,
            "total_quantity": 100,
            "good_quantity": 95,
            "reject_quantity": 5,
            "ideal_cycle_time_seconds": 5.0,
        },
    )

    assert response.status_code == 201

    production_run = response.json()

    assert (
        production_run["production_line_id"]
        == hierarchy["production_line_id"]
    )

    assert production_run["status"] == "running"
    assert production_run["target_quantity"] == 1000
    assert production_run["total_quantity"] == 100
    assert production_run["good_quantity"] == 95
    assert production_run["reject_quantity"] == 5
    assert production_run["ideal_cycle_time_seconds"] == 5.0


async def test_create_production_run_returns_404_for_missing_line(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    response = await client.post(
        "/production-runs",
        headers=auth_headers["admin"],
        json={
            "production_line_id": 999999,
            "started_at": "2026-08-25T08:00:00Z",
            "status": "running",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Production line not found"
    }


@pytest.mark.parametrize(
    "role_name",
    [
        "admin",
        "manager",
        "technician",
        "operator",
    ],
)
async def test_all_roles_can_read_production_runs(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
    role_name: str,
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    production_run = await create_test_production_run(
        client,
        auth_headers["admin"],
        hierarchy["production_line_id"],
    )

    response = await client.get(
        f"/production-runs/{production_run['id']}",
        headers=auth_headers[role_name],
    )

    assert response.status_code == 200
    assert response.json()["id"] == production_run["id"]


async def test_operator_cannot_create_production_run(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    response = await client.post(
        "/production-runs",
        headers=auth_headers["operator"],
        json={
            "production_line_id": hierarchy["production_line_id"],
            "started_at": "2026-08-25T08:00:00Z",
            "status": "running",
        },
    )

    assert response.status_code == 403


async def test_create_downtime_event_for_machine_on_same_line(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    production_run = await create_test_production_run(
        client,
        auth_headers["admin"],
        hierarchy["production_line_id"],
    )

    response = await client.post(
        "/downtime-events",
        headers=auth_headers["operator"],
        json={
            "production_run_id": production_run["id"],
            "machine_id": hierarchy["machine_id"],
            "category": "unplanned",
            "reason": "Motor overload",
            "started_at": "2026-08-25T10:00:00Z",
            "ended_at": "2026-08-25T10:15:00Z",
            "notes": "Machine stopped automatically",
        },
    )

    assert response.status_code == 201

    downtime_event = response.json()

    assert (
        downtime_event["production_run_id"]
        == production_run["id"]
    )

    assert downtime_event["machine_id"] == hierarchy["machine_id"]
    assert downtime_event["category"] == "unplanned"
    assert downtime_event["reason"] == "Motor overload"


async def test_downtime_event_returns_404_for_missing_run(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    response = await client.post(
        "/downtime-events",
        headers=auth_headers["admin"],
        json={
            "production_run_id": 999999,
            "machine_id": None,
            "category": "planned",
            "reason": "Scheduled cleaning",
            "started_at": "2026-08-25T10:00:00Z",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Production run not found"
    }


async def test_downtime_event_returns_404_for_missing_machine(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    production_run = await create_test_production_run(
        client,
        auth_headers["admin"],
        hierarchy["production_line_id"],
    )

    response = await client.post(
        "/downtime-events",
        headers=auth_headers["admin"],
        json={
            "production_run_id": production_run["id"],
            "machine_id": 999999,
            "category": "unplanned",
            "reason": "Machine failure",
            "started_at": "2026-08-25T10:00:00Z",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Machine not found"
    }


async def test_downtime_event_rejects_machine_from_another_line(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    production_run = await create_test_production_run(
        client,
        auth_headers["admin"],
        hierarchy["production_line_id"],
    )

    second_line_response = await client.post(
        "/production-lines",
        headers=auth_headers["admin"],
        json={
            "area_id": hierarchy["area_id"],
            "name": "Assembly Line B",
            "code": "LINE-B",
            "description": "Secondary assembly line",
        },
    )

    assert second_line_response.status_code == 201
    second_line_id = second_line_response.json()["id"]

    second_machine_response = await client.post(
        "/machines",
        headers=auth_headers["admin"],
        json={
            "area_id": hierarchy["area_id"],
            "production_line_id": second_line_id,
            "name": "Assembly Machine B",
            "code": "MACHINE-B",
            "location": "Assembly Line B",
            "status": "active",
        },
    )

    assert second_machine_response.status_code == 201
    second_machine_id = second_machine_response.json()["id"]

    response = await client.post(
        "/downtime-events",
        headers=auth_headers["admin"],
        json={
            "production_run_id": production_run["id"],
            "machine_id": second_machine_id,
            "category": "unplanned",
            "reason": "Wrong-line machine test",
            "started_at": "2026-08-25T10:00:00Z",
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "Machine does not belong to the "
            "production run's production line"
        )
    }


async def test_manager_cannot_create_downtime_event(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    production_run = await create_test_production_run(
        client,
        auth_headers["admin"],
        hierarchy["production_line_id"],
    )

    response = await client.post(
        "/downtime-events",
        headers=auth_headers["manager"],
        json={
            "production_run_id": production_run["id"],
            "machine_id": hierarchy["machine_id"],
            "category": "unplanned",
            "reason": "Permission test",
            "started_at": "2026-08-25T10:00:00Z",
        },
    )

    assert response.status_code == 403



async def test_complete_production_run(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    production_run = await create_test_production_run(
        client,
        auth_headers["admin"],
        hierarchy["production_line_id"],
    )

    response = await client.patch(
        f"/production-runs/{production_run['id']}",
        headers=auth_headers["admin"],
        json={
            "status": "completed",
            "ended_at": "2026-08-25T16:00:00Z",
            "total_quantity": 1000,
            "good_quantity": 970,
            "reject_quantity": 30,
        },
    )

    assert response.status_code == 200

    updated_run = response.json()

    assert updated_run["status"] == "completed"
    assert updated_run["ended_at"] is not None
    assert updated_run["total_quantity"] == 1000
    assert updated_run["good_quantity"] == 970
    assert updated_run["reject_quantity"] == 30


async def test_completed_production_run_cannot_be_modified(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    production_run = await create_test_production_run(
        client,
        auth_headers["admin"],
        hierarchy["production_line_id"],
    )

    completion_response = await client.patch(
        f"/production-runs/{production_run['id']}",
        headers=auth_headers["admin"],
        json={
            "status": "completed",
            "ended_at": "2026-08-25T16:00:00Z",
        },
    )

    assert completion_response.status_code == 200

    response = await client.patch(
        f"/production-runs/{production_run['id']}",
        headers=auth_headers["admin"],
        json={
            "total_quantity": 1200,
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": (
            "Completed or cancelled production runs "
            "cannot be modified"
        )
    }


async def test_production_run_update_validates_final_quantities(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    response = await client.post(
        "/production-runs",
        headers=auth_headers["admin"],
        json={
            "production_line_id": hierarchy["production_line_id"],
            "started_at": "2026-08-25T08:00:00Z",
            "status": "running",
            "total_quantity": 100,
            "good_quantity": 90,
            "reject_quantity": 10,
            "ideal_cycle_time_seconds": 5.0,
        },
    )

    assert response.status_code == 201

    production_run_id = response.json()["id"]

    response = await client.patch(
        f"/production-runs/{production_run_id}",
        headers=auth_headers["admin"],
        json={
            "total_quantity": 80,
        },
    )

    assert response.status_code == 422

    assert (
        "good_quantity and reject_quantity "
        "cannot exceed total_quantity"
        in response.json()["detail"]
    )


async def test_running_production_run_cannot_have_ended_at(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    production_run = await create_test_production_run(
        client,
        auth_headers["admin"],
        hierarchy["production_line_id"],
    )

    response = await client.patch(
        f"/production-runs/{production_run['id']}",
        headers=auth_headers["admin"],
        json={
            "ended_at": "2026-08-25T16:00:00Z",
        },
    )

    assert response.status_code == 422

    assert (
        "running production runs cannot have ended_at"
        in response.json()["detail"]
    )


async def test_operator_cannot_update_production_run(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    production_run = await create_test_production_run(
        client,
        auth_headers["admin"],
        hierarchy["production_line_id"],
    )

    response = await client.patch(
        f"/production-runs/{production_run['id']}",
        headers=auth_headers["operator"],
        json={
            "total_quantity": 100,
        },
    )

    assert response.status_code == 403


async def test_downtime_cannot_start_before_production_run(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    production_run = await create_test_production_run(
        client,
        auth_headers["admin"],
        hierarchy["production_line_id"],
    )

    response = await client.post(
        "/downtime-events",
        headers=auth_headers["operator"],
        json={
            "production_run_id": production_run["id"],
            "machine_id": hierarchy["machine_id"],
            "category": "unplanned",
            "reason": "Early downtime",
            "started_at": "2026-08-25T07:30:00Z",
            "ended_at": "2026-08-25T08:10:00Z",
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "Downtime event cannot start before "
            "the production run"
        )
    }


async def test_completed_run_downtime_requires_ended_at(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    production_run = await create_test_production_run(
        client,
        auth_headers["admin"],
        hierarchy["production_line_id"],
    )

    completion_response = await client.patch(
        f"/production-runs/{production_run['id']}",
        headers=auth_headers["admin"],
        json={
            "status": "completed",
            "ended_at": "2026-08-25T16:00:00Z",
        },
    )

    assert completion_response.status_code == 200

    response = await client.post(
        "/downtime-events",
        headers=auth_headers["operator"],
        json={
            "production_run_id": production_run["id"],
            "machine_id": hierarchy["machine_id"],
            "category": "unplanned",
            "reason": "Open downtime on completed run",
            "started_at": "2026-08-25T15:00:00Z",
            "ended_at": None,
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "Downtime event requires ended_at when "
            "the production run has ended"
        )
    }


async def test_downtime_cannot_end_after_production_run(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    production_run = await create_test_production_run(
        client,
        auth_headers["admin"],
        hierarchy["production_line_id"],
    )

    completion_response = await client.patch(
        f"/production-runs/{production_run['id']}",
        headers=auth_headers["admin"],
        json={
            "status": "completed",
            "ended_at": "2026-08-25T16:00:00Z",
        },
    )

    assert completion_response.status_code == 200

    response = await client.post(
        "/downtime-events",
        headers=auth_headers["operator"],
        json={
            "production_run_id": production_run["id"],
            "machine_id": hierarchy["machine_id"],
            "category": "unplanned",
            "reason": "Late downtime",
            "started_at": "2026-08-25T15:50:00Z",
            "ended_at": "2026-08-25T16:10:00Z",
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "Downtime event cannot end after "
            "the production run ended"
        )
    }

async def test_open_downtime_event_can_be_closed(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    production_run = await create_test_production_run(
        client,
        auth_headers["admin"],
        hierarchy["production_line_id"],
    )

    create_response = await client.post(
        "/downtime-events",
        headers=auth_headers["operator"],
        json={
            "production_run_id": production_run["id"],
            "machine_id": hierarchy["machine_id"],
            "category": "unplanned",
            "reason": "Bearing failure",
            "started_at": "2026-08-25T10:00:00Z",
            "ended_at": None,
        },
    )

    assert create_response.status_code == 201

    downtime_event_id = create_response.json()["id"]

    close_response = await client.patch(
        f"/downtime-events/{downtime_event_id}",
        headers=auth_headers["operator"],
        json={
            "ended_at": "2026-08-25T10:20:00Z",
        },
    )

    assert close_response.status_code == 200

    closed_event = close_response.json()

    assert closed_event["ended_at"] is not None
    assert closed_event["reason"] == "Bearing failure"


async def test_closed_downtime_event_cannot_be_modified(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    production_run = await create_test_production_run(
        client,
        auth_headers["admin"],
        hierarchy["production_line_id"],
    )

    create_response = await client.post(
        "/downtime-events",
        headers=auth_headers["operator"],
        json={
            "production_run_id": production_run["id"],
            "machine_id": hierarchy["machine_id"],
            "category": "unplanned",
            "reason": "Electrical fault",
            "started_at": "2026-08-25T11:00:00Z",
            "ended_at": None,
        },
    )

    assert create_response.status_code == 201

    downtime_event_id = create_response.json()["id"]

    close_response = await client.patch(
        f"/downtime-events/{downtime_event_id}",
        headers=auth_headers["operator"],
        json={
            "ended_at": "2026-08-25T11:15:00Z",
        },
    )

    assert close_response.status_code == 200

    response = await client.patch(
        f"/downtime-events/{downtime_event_id}",
        headers=auth_headers["operator"],
        json={
            "notes": "Attempted historical modification",
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": "Closed downtime events cannot be modified"
    }


async def test_production_run_cannot_complete_with_open_downtime(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    production_run = await create_test_production_run(
        client,
        auth_headers["admin"],
        hierarchy["production_line_id"],
    )

    downtime_response = await client.post(
        "/downtime-events",
        headers=auth_headers["operator"],
        json={
            "production_run_id": production_run["id"],
            "machine_id": hierarchy["machine_id"],
            "category": "unplanned",
            "reason": "Open machine failure",
            "started_at": "2026-08-25T14:00:00Z",
            "ended_at": None,
        },
    )

    assert downtime_response.status_code == 201

    response = await client.patch(
        f"/production-runs/{production_run['id']}",
        headers=auth_headers["admin"],
        json={
            "status": "completed",
            "ended_at": "2026-08-25T16:00:00Z",
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": (
            "Production run cannot end while "
            "downtime events are still open"
        )
    }


async def test_production_run_can_complete_after_downtime_is_closed(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    production_run = await create_test_production_run(
        client,
        auth_headers["admin"],
        hierarchy["production_line_id"],
    )

    downtime_response = await client.post(
        "/downtime-events",
        headers=auth_headers["operator"],
        json={
            "production_run_id": production_run["id"],
            "machine_id": hierarchy["machine_id"],
            "category": "unplanned",
            "reason": "Short machine stop",
            "started_at": "2026-08-25T12:00:00Z",
            "ended_at": None,
        },
    )

    assert downtime_response.status_code == 201

    downtime_event_id = downtime_response.json()["id"]

    close_response = await client.patch(
        f"/downtime-events/{downtime_event_id}",
        headers=auth_headers["operator"],
        json={
            "ended_at": "2026-08-25T12:20:00Z",
        },
    )

    assert close_response.status_code == 200

    completion_response = await client.patch(
        f"/production-runs/{production_run['id']}",
        headers=auth_headers["admin"],
        json={
            "status": "completed",
            "ended_at": "2026-08-25T16:00:00Z",
        },
    )

    assert completion_response.status_code == 200
    assert completion_response.json()["status"] == "completed"


async def test_production_run_cannot_end_before_closed_downtime(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    production_run = await create_test_production_run(
        client,
        auth_headers["admin"],
        hierarchy["production_line_id"],
    )

    downtime_response = await client.post(
        "/downtime-events",
        headers=auth_headers["operator"],
        json={
            "production_run_id": production_run["id"],
            "machine_id": hierarchy["machine_id"],
            "category": "unplanned",
            "reason": "Late machine stop",
            "started_at": "2026-08-25T15:50:00Z",
            "ended_at": "2026-08-25T16:15:00Z",
        },
    )

    assert downtime_response.status_code == 201

    response = await client.patch(
        f"/production-runs/{production_run['id']}",
        headers=auth_headers["admin"],
        json={
            "status": "completed",
            "ended_at": "2026-08-25T16:00:00Z",
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": (
            "Production run cannot end before "
            "its downtime events"
        )
    }

async def create_completed_oee_test_run(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> dict:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    production_run = await create_test_production_run(
        client,
        auth_headers["admin"],
        hierarchy["production_line_id"],
    )

    planned_response = await client.post(
        "/downtime-events",
        headers=auth_headers["operator"],
        json={
            "production_run_id": production_run["id"],
            "machine_id": None,
            "category": "planned",
            "reason": "Scheduled changeover",
            "started_at": "2026-08-25T09:00:00Z",
            "ended_at": "2026-08-25T09:30:00Z",
        },
    )

    assert planned_response.status_code == 201

    unplanned_response = await client.post(
        "/downtime-events",
        headers=auth_headers["operator"],
        json={
            "production_run_id": production_run["id"],
            "machine_id": hierarchy["machine_id"],
            "category": "unplanned",
            "reason": "Machine failure",
            "started_at": "2026-08-25T13:00:00Z",
            "ended_at": "2026-08-25T13:45:00Z",
        },
    )

    assert unplanned_response.status_code == 201

    completion_response = await client.patch(
        f"/production-runs/{production_run['id']}",
        headers=auth_headers["admin"],
        json={
            "status": "completed",
            "ended_at": "2026-08-25T16:00:00Z",
            "total_quantity": 1000,
            "good_quantity": 950,
            "reject_quantity": 50,
            "ideal_cycle_time_seconds": 20.0,
        },
    )

    assert completion_response.status_code == 200

    return completion_response.json()


async def test_get_production_run_oee(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    production_run = await create_completed_oee_test_run(
        client,
        auth_headers,
    )

    response = await client.get(
        f"/production-runs/{production_run['id']}/oee",
        headers=auth_headers["admin"],
    )

    assert response.status_code == 200

    metrics = response.json()

    assert metrics["production_run_id"] == production_run["id"]

    assert metrics["scheduled_time_seconds"] == pytest.approx(
        28800
    )

    assert metrics["planned_downtime_seconds"] == pytest.approx(
        1800
    )

    assert metrics["planned_production_time_seconds"] == pytest.approx(
        27000
    )

    assert metrics["unplanned_downtime_seconds"] == pytest.approx(
        2700
    )

    assert metrics["operating_time_seconds"] == pytest.approx(
        24300
    )

    assert metrics["availability"] == pytest.approx(
        24300 / 27000
    )

    assert metrics["performance"] == pytest.approx(
        20000 / 24300
    )

    assert metrics["quality"] == pytest.approx(
        0.95
    )

    assert metrics["oee"] == pytest.approx(
        (24300 / 27000)
        * (20000 / 24300)
        * 0.95
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
async def test_all_roles_can_read_oee(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
    role_name: str,
) -> None:
    production_run = await create_completed_oee_test_run(
        client,
        auth_headers,
    )

    response = await client.get(
        f"/production-runs/{production_run['id']}/oee",
        headers=auth_headers[role_name],
    )

    assert response.status_code == 200

    assert (
        response.json()["production_run_id"]
        == production_run["id"]
    )


async def test_oee_returns_404_for_missing_production_run(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    response = await client.get(
        "/production-runs/999999/oee",
        headers=auth_headers["admin"],
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Production run not found"
    }


async def test_oee_rejects_running_production_run(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    production_run = await create_test_production_run(
        client,
        auth_headers["admin"],
        hierarchy["production_line_id"],
    )

    response = await client.get(
        f"/production-runs/{production_run['id']}/oee",
        headers=auth_headers["admin"],
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": (
            "OEE can only be calculated for "
            "completed production runs"
        )
    }


async def test_oee_rejects_cancelled_production_run(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    production_run = await create_test_production_run(
        client,
        auth_headers["admin"],
        hierarchy["production_line_id"],
    )

    cancellation_response = await client.patch(
        f"/production-runs/{production_run['id']}",
        headers=auth_headers["admin"],
        json={
            "status": "cancelled",
            "ended_at": "2026-08-25T12:00:00Z",
        },
    )

    assert cancellation_response.status_code == 200

    response = await client.get(
        f"/production-runs/{production_run['id']}/oee",
        headers=auth_headers["admin"],
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": (
            "OEE can only be calculated for "
            "completed production runs"
        )
    }



async def create_completed_line_analytics_run(
    client: AsyncClient,
    admin_headers: dict[str, str],
    production_line_id: int,
    *,
    started_at: str,
    ended_at: str,
    ideal_cycle_time_seconds: float,
    total_quantity: int,
    good_quantity: int,
) -> dict:
    response = await client.post(
        "/production-runs",
        headers=admin_headers,
        json={
            "production_line_id": production_line_id,
            "started_at": started_at,
            "ended_at": ended_at,
            "status": "completed",
            "target_quantity": None,
            "total_quantity": total_quantity,
            "good_quantity": good_quantity,
            "reject_quantity": (
                total_quantity - good_quantity
            ),
            "ideal_cycle_time_seconds": (
                ideal_cycle_time_seconds
            ),
        },
    )

    assert response.status_code == 201

    return response.json()


async def test_get_production_line_aggregated_oee(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]

    first_run = await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T09:00:00Z",
        ideal_cycle_time_seconds=10.0,
        total_quantity=180,
        good_quantity=180,
    )

    second_run = await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-21T08:00:00Z",
        ended_at="2026-08-21T12:00:00Z",
        ideal_cycle_time_seconds=20.0,
        total_quantity=180,
        good_quantity=90,
    )

    response = await client.get(
        f"/production-lines/{line_id}/oee",
        headers=auth_headers["admin"],
    )

    assert response.status_code == 200

    metrics = response.json()

    assert metrics["production_line_id"] == line_id
    assert metrics["start_at"] is None
    assert metrics["end_at"] is None

    assert metrics["run_count"] == 2

    assert metrics["scheduled_time_seconds"] == pytest.approx(
        18000
    )

    assert metrics["planned_downtime_seconds"] == 0
    assert metrics["planned_production_time_seconds"] == pytest.approx(
        18000
    )

    assert metrics["unplanned_downtime_seconds"] == 0
    assert metrics["operating_time_seconds"] == pytest.approx(
        18000
    )

    assert metrics["total_quantity"] == 360
    assert metrics["good_quantity"] == 270

    assert metrics["availability"] == pytest.approx(
        1.0
    )

    # Run 1 ideal production time:
    # 10 seconds × 180 units = 1800 seconds
    #
    # Run 2 ideal production time:
    # 20 seconds × 180 units = 3600 seconds
    #
    # Aggregated ideal production time = 5400 seconds.
    assert metrics["performance"] == pytest.approx(
        5400 / 18000
    )

    assert metrics["quality"] == pytest.approx(
        270 / 360
    )

    assert metrics["oee"] == pytest.approx(
        1.0
        * (5400 / 18000)
        * (270 / 360)
    )

    first_oee_response = await client.get(
        f"/production-runs/{first_run['id']}/oee",
        headers=auth_headers["admin"],
    )

    second_oee_response = await client.get(
        f"/production-runs/{second_run['id']}/oee",
        headers=auth_headers["admin"],
    )

    assert first_oee_response.status_code == 200
    assert second_oee_response.status_code == 200

    naive_average = (
        first_oee_response.json()["oee"]
        + second_oee_response.json()["oee"]
    ) / 2

    assert metrics["oee"] != pytest.approx(
        naive_average
    )


async def test_line_oee_excludes_running_and_cancelled_runs(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]

    await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T10:00:00Z",
        ideal_cycle_time_seconds=10.0,
        total_quantity=500,
        good_quantity=450,
    )

    running_response = await client.post(
        "/production-runs",
        headers=auth_headers["admin"],
        json={
            "production_line_id": line_id,
            "started_at": "2026-08-22T08:00:00Z",
            "status": "running",
            "total_quantity": 200,
            "good_quantity": 190,
            "reject_quantity": 10,
            "ideal_cycle_time_seconds": 10.0,
        },
    )

    assert running_response.status_code == 201

    cancelled_response = await client.post(
        "/production-runs",
        headers=auth_headers["admin"],
        json={
            "production_line_id": line_id,
            "started_at": "2026-08-21T08:00:00Z",
            "ended_at": "2026-08-21T09:00:00Z",
            "status": "cancelled",
            "total_quantity": 100,
            "good_quantity": 90,
            "reject_quantity": 10,
            "ideal_cycle_time_seconds": 10.0,
        },
    )

    assert cancelled_response.status_code == 201

    response = await client.get(
        f"/production-lines/{line_id}/oee",
        headers=auth_headers["admin"],
    )

    assert response.status_code == 200

    metrics = response.json()

    assert metrics["run_count"] == 1
    assert metrics["total_quantity"] == 500
    assert metrics["good_quantity"] == 450


async def test_line_oee_filters_completed_runs_by_date_range(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]

    await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T10:00:00Z",
        ideal_cycle_time_seconds=10.0,
        total_quantity=100,
        good_quantity=90,
    )

    await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-21T08:00:00Z",
        ended_at="2026-08-21T12:00:00Z",
        ideal_cycle_time_seconds=20.0,
        total_quantity=200,
        good_quantity=180,
    )

    response = await client.get(
        f"/production-lines/{line_id}/oee",
        headers=auth_headers["admin"],
        params={
            "start_at": "2026-08-21T00:00:00Z",
            "end_at": "2026-08-22T00:00:00Z",
        },
    )

    assert response.status_code == 200

    metrics = response.json()

    assert metrics["run_count"] == 1

    assert metrics["total_quantity"] == 200
    assert metrics["good_quantity"] == 180

    assert metrics["start_at"] is not None
    assert metrics["end_at"] is not None


@pytest.mark.parametrize(
    "role_name",
    [
        "admin",
        "manager",
        "technician",
        "operator",
    ],
)
async def test_all_roles_can_read_production_line_oee(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
    role_name: str,
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]

    await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T10:00:00Z",
        ideal_cycle_time_seconds=10.0,
        total_quantity=500,
        good_quantity=450,
    )

    response = await client.get(
        f"/production-lines/{line_id}/oee",
        headers=auth_headers[role_name],
    )

    assert response.status_code == 200
    assert response.json()["run_count"] == 1


async def test_line_oee_returns_404_for_missing_line(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    response = await client.get(
        "/production-lines/999999/oee",
        headers=auth_headers["admin"],
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Production line not found"
    }


async def test_line_oee_returns_422_when_no_completed_runs_exist(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    response = await client.get(
        (
            f"/production-lines/"
            f"{hierarchy['production_line_id']}/oee"
        ),
        headers=auth_headers["admin"],
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": (
            "No completed production runs found "
            "for the selected period"
        )
    }


async def test_line_oee_returns_422_for_empty_selected_period(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]

    await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T10:00:00Z",
        ideal_cycle_time_seconds=10.0,
        total_quantity=500,
        good_quantity=450,
    )

    response = await client.get(
        f"/production-lines/{line_id}/oee",
        headers=auth_headers["admin"],
        params={
            "start_at": "2026-09-01T00:00:00Z",
            "end_at": "2026-09-02T00:00:00Z",
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": (
            "No completed production runs found "
            "for the selected period"
        )
    }


async def test_line_oee_rejects_invalid_date_range(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    response = await client.get(
        (
            f"/production-lines/"
            f"{hierarchy['production_line_id']}/oee"
        ),
        headers=auth_headers["admin"],
        params={
            "start_at": "2026-08-22T00:00:00Z",
            "end_at": "2026-08-21T00:00:00Z",
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": "end_at must be later than start_at"
    }


async def create_line_analytics_downtime(
    client: AsyncClient,
    admin_headers: dict[str, str],
    production_run_id: int,
    *,
    reason: str,
    category: str,
    started_at: str,
    ended_at: str,
    machine_id: int | None = None,
) -> dict:
    response = await client.post(
        "/downtime-events",
        headers=admin_headers,
        json={
            "production_run_id": production_run_id,
            "machine_id": machine_id,
            "category": category,
            "reason": reason,
            "started_at": started_at,
            "ended_at": ended_at,
            "notes": None,
        },
    )

    assert response.status_code == 201

    return response.json()


async def test_get_production_line_downtime_analytics(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]
    machine_id = hierarchy["machine_id"]

    production_run = await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T12:00:00Z",
        ideal_cycle_time_seconds=10.0,
        total_quantity=500,
        good_quantity=450,
    )

    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason="Motor Failure",
        category="unplanned",
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T09:00:00Z",
        machine_id=machine_id,
    )

    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason=" motor failure ",
        category="unplanned",
        started_at="2026-08-20T09:30:00Z",
        ended_at="2026-08-20T10:00:00Z",
        machine_id=machine_id,
    )

    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason="Changeover",
        category="planned",
        started_at="2026-08-20T08:30:00Z",
        ended_at="2026-08-20T09:30:00Z",
        machine_id=None,
    )

    response = await client.get(
        f"/production-lines/{line_id}/downtime-analytics",
        headers=auth_headers["admin"],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["production_line_id"] == line_id
    assert data["start_at"] is None
    assert data["end_at"] is None

    assert data["run_count"] == 1
    assert data["event_count"] == 3

    # Recorded event duration:
    #
    # Motor failure 1 = 3600 sec
    # Motor failure 2 = 1800 sec
    # Changeover      = 3600 sec
    #
    # Total = 9000 sec.
    #
    # The Changeover overlaps the first Motor Failure,
    # but Pareto analytics intentionally keeps recorded
    # event duration rather than merging intervals.
    assert data["recorded_downtime_seconds"] == pytest.approx(
        9000
    )

    assert data["planned_downtime_seconds"] == pytest.approx(
        3600
    )

    assert data["unplanned_downtime_seconds"] == pytest.approx(
        5400
    )

    assert len(data["by_reason"]) == 2

    motor_failure = data["by_reason"][0]

    assert motor_failure["reason"] == "Motor Failure"
    assert motor_failure["event_count"] == 2
    assert motor_failure["duration_seconds"] == pytest.approx(
        5400
    )
    assert motor_failure["percentage"] == pytest.approx(
        5400 / 9000
    )

    changeover = data["by_reason"][1]

    assert changeover["reason"] == "Changeover"
    assert changeover["event_count"] == 1
    assert changeover["duration_seconds"] == pytest.approx(
        3600
    )
    assert changeover["percentage"] == pytest.approx(
        3600 / 9000
    )

    assert len(data["by_machine"]) == 2

    machine_breakdown = data["by_machine"][0]

    assert machine_breakdown["machine_id"] == machine_id
    assert machine_breakdown["event_count"] == 2
    assert machine_breakdown[
        "duration_seconds"
    ] == pytest.approx(
        5400
    )
    assert machine_breakdown["percentage"] == pytest.approx(
        5400 / 9000
    )

    line_wide_breakdown = data["by_machine"][1]

    assert line_wide_breakdown["machine_id"] is None
    assert line_wide_breakdown["event_count"] == 1
    assert line_wide_breakdown[
        "duration_seconds"
    ] == pytest.approx(
        3600
    )


async def test_line_downtime_analytics_supports_zero_downtime(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]

    await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T10:00:00Z",
        ideal_cycle_time_seconds=10.0,
        total_quantity=500,
        good_quantity=480,
    )

    response = await client.get(
        f"/production-lines/{line_id}/downtime-analytics",
        headers=auth_headers["admin"],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["run_count"] == 1
    assert data["event_count"] == 0

    assert data["recorded_downtime_seconds"] == 0.0
    assert data["planned_downtime_seconds"] == 0.0
    assert data["unplanned_downtime_seconds"] == 0.0

    assert data["by_reason"] == []
    assert data["by_machine"] == []


async def test_line_downtime_analytics_filters_by_date_range(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]
    machine_id = hierarchy["machine_id"]

    first_run = await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T10:00:00Z",
        ideal_cycle_time_seconds=10.0,
        total_quantity=300,
        good_quantity=280,
    )

    second_run = await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-21T08:00:00Z",
        ended_at="2026-08-21T12:00:00Z",
        ideal_cycle_time_seconds=10.0,
        total_quantity=500,
        good_quantity=470,
    )

    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        first_run["id"],
        reason="Old Failure",
        category="unplanned",
        started_at="2026-08-20T08:30:00Z",
        ended_at="2026-08-20T09:30:00Z",
        machine_id=machine_id,
    )

    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        second_run["id"],
        reason="Selected Failure",
        category="unplanned",
        started_at="2026-08-21T09:00:00Z",
        ended_at="2026-08-21T11:00:00Z",
        machine_id=machine_id,
    )

    response = await client.get(
        f"/production-lines/{line_id}/downtime-analytics",
        headers=auth_headers["admin"],
        params={
            "start_at": "2026-08-21T00:00:00Z",
            "end_at": "2026-08-22T00:00:00Z",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["run_count"] == 1
    assert data["event_count"] == 1

    assert data["recorded_downtime_seconds"] == pytest.approx(
        7200
    )

    assert len(data["by_reason"]) == 1
    assert data["by_reason"][0]["reason"] == "Selected Failure"

    assert data["start_at"] is not None
    assert data["end_at"] is not None


@pytest.mark.parametrize(
    "role_name",
    [
        "admin",
        "manager",
        "technician",
        "operator",
    ],
)
async def test_all_roles_can_read_line_downtime_analytics(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
    role_name: str,
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]

    await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T10:00:00Z",
        ideal_cycle_time_seconds=10.0,
        total_quantity=500,
        good_quantity=480,
    )

    response = await client.get(
        f"/production-lines/{line_id}/downtime-analytics",
        headers=auth_headers[role_name],
    )

    assert response.status_code == 200
    assert response.json()["run_count"] == 1


async def test_line_downtime_analytics_returns_404_for_missing_line(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    response = await client.get(
        "/production-lines/999999/downtime-analytics",
        headers=auth_headers["admin"],
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Production line not found"
    }


async def test_line_downtime_analytics_requires_completed_runs(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]

    response = await client.get(
        f"/production-lines/{line_id}/downtime-analytics",
        headers=auth_headers["admin"],
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": (
            "No completed production runs found "
            "for the selected period"
        )
    }


async def test_line_downtime_analytics_rejects_invalid_date_range(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]

    response = await client.get(
        f"/production-lines/{line_id}/downtime-analytics",
        headers=auth_headers["admin"],
        params={
            "start_at": "2026-08-22T00:00:00Z",
            "end_at": "2026-08-21T00:00:00Z",
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": "end_at must be later than start_at"
    }




async def test_production_run_rejects_overlap_on_same_line(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]

    await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T12:00:00Z",
        ideal_cycle_time_seconds=10.0,
        total_quantity=500,
        good_quantity=480,
    )

    response = await client.post(
        "/production-runs",
        headers=auth_headers["admin"],
        json={
            "production_line_id": line_id,
            "started_at": "2026-08-20T10:00:00Z",
            "ended_at": "2026-08-20T14:00:00Z",
            "status": "completed",
            "total_quantity": 300,
            "good_quantity": 290,
            "reject_quantity": 10,
            "ideal_cycle_time_seconds": 10.0,
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": (
            "Production run overlaps an existing run "
            "on the same production line"
        )
    }


async def test_production_run_allows_touching_boundaries(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]

    first_run = await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T12:00:00Z",
        ideal_cycle_time_seconds=10.0,
        total_quantity=500,
        good_quantity=480,
    )

    second_response = await client.post(
        "/production-runs",
        headers=auth_headers["admin"],
        json={
            "production_line_id": line_id,
            "started_at": "2026-08-20T12:00:00Z",
            "ended_at": "2026-08-20T16:00:00Z",
            "status": "completed",
            "total_quantity": 400,
            "good_quantity": 390,
            "reject_quantity": 10,
            "ideal_cycle_time_seconds": 10.0,
        },
    )

    assert first_run["id"] is not None

    assert second_response.status_code == 201


async def test_open_production_run_blocks_later_run_on_same_line(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]

    running_response = await client.post(
        "/production-runs",
        headers=auth_headers["admin"],
        json={
            "production_line_id": line_id,
            "started_at": "2026-08-20T08:00:00Z",
            "status": "running",
            "total_quantity": 0,
            "good_quantity": 0,
            "reject_quantity": 0,
            "ideal_cycle_time_seconds": 10.0,
        },
    )

    assert running_response.status_code == 201

    response = await client.post(
        "/production-runs",
        headers=auth_headers["admin"],
        json={
            "production_line_id": line_id,
            "started_at": "2026-08-21T08:00:00Z",
            "ended_at": "2026-08-21T12:00:00Z",
            "status": "completed",
            "total_quantity": 300,
            "good_quantity": 290,
            "reject_quantity": 10,
            "ideal_cycle_time_seconds": 10.0,
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": (
            "Production run overlaps an existing run "
            "on the same production line"
        )
    }



async def test_database_rejects_overlapping_production_runs(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]

    async with AsyncSessionLocal() as db:
        first_run = ProductionRun(
            production_line_id=line_id,
            started_at=datetime(
                2026,
                8,
                20,
                8,
                0,
                tzinfo=timezone.utc,
            ),
            ended_at=datetime(
                2026,
                8,
                20,
                12,
                0,
                tzinfo=timezone.utc,
            ),
            status="completed",
            total_quantity=500,
            good_quantity=480,
            reject_quantity=20,
            ideal_cycle_time_seconds=10.0,
        )

        db.add(first_run)
        await db.commit()

        overlapping_run = ProductionRun(
            production_line_id=line_id,
            started_at=datetime(
                2026,
                8,
                20,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            ended_at=datetime(
                2026,
                8,
                20,
                14,
                0,
                tzinfo=timezone.utc,
            ),
            status="completed",
            total_quantity=300,
            good_quantity=290,
            reject_quantity=10,
            ideal_cycle_time_seconds=10.0,
        )

        db.add(overlapping_run)

        with pytest.raises(IntegrityError) as exc_info:
            await db.commit()

        await db.rollback()

    assert (
        "ex_production_runs_line_time_overlap"
        in str(exc_info.value)
    )




async def test_database_overlap_fallback_returns_422(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.services.production_run_service as production_run_service

    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]

    await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T12:00:00Z",
        ideal_cycle_time_seconds=10.0,
        total_quantity=500,
        good_quantity=480,
    )

    async def bypass_overlap_validation(
        *args,
        **kwargs,
    ) -> None:
        return None

    monkeypatch.setattr(
        production_run_service,
        "validate_production_run_overlap",
        bypass_overlap_validation,
    )

    response = await client.post(
        "/production-runs",
        headers=auth_headers["admin"],
        json={
            "production_line_id": line_id,
            "started_at": "2026-08-20T10:00:00Z",
            "ended_at": "2026-08-20T14:00:00Z",
            "status": "completed",
            "total_quantity": 300,
            "good_quantity": 290,
            "reject_quantity": 10,
            "ideal_cycle_time_seconds": 10.0,
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": (
            "Production run overlaps an existing run "
            "on the same production line"
        )
    }


async def test_database_rejects_negative_production_quantity(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    async with AsyncSessionLocal() as db:
        production_run = ProductionRun(
            production_line_id=hierarchy["production_line_id"],
            started_at=datetime(
                2026,
                8,
                20,
                8,
                0,
                tzinfo=timezone.utc,
            ),
            ended_at=datetime(
                2026,
                8,
                20,
                12,
                0,
                tzinfo=timezone.utc,
            ),
            status="completed",
            total_quantity=-1,
            good_quantity=0,
            reject_quantity=0,
            ideal_cycle_time_seconds=10.0,
        )

        db.add(production_run)

        with pytest.raises(IntegrityError) as exc_info:
            await db.commit()

        await db.rollback()

    error_text = str(exc_info.value)

    assert "violates check constraint" in error_text

    assert (
        "ck_production_runs_total_quantity_nonnegative"
        in error_text
        or
        "ck_production_runs_quantity_consistency"
        in error_text
    )


async def test_database_rejects_inconsistent_production_quantities(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    async with AsyncSessionLocal() as db:
        production_run = ProductionRun(
            production_line_id=hierarchy["production_line_id"],
            started_at=datetime(
                2026,
                8,
                20,
                8,
                0,
                tzinfo=timezone.utc,
            ),
            ended_at=datetime(
                2026,
                8,
                20,
                12,
                0,
                tzinfo=timezone.utc,
            ),
            status="completed",
            total_quantity=100,
            good_quantity=90,
            reject_quantity=20,
            ideal_cycle_time_seconds=10.0,
        )

        db.add(production_run)

        with pytest.raises(IntegrityError) as exc_info:
            await db.commit()

        await db.rollback()

    assert (
        "ck_production_runs_quantity_consistency"
        in str(exc_info.value)
    )


async def test_database_rejects_invalid_production_status(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    async with AsyncSessionLocal() as db:
        production_run = ProductionRun(
            production_line_id=hierarchy["production_line_id"],
            started_at=datetime(
                2026,
                8,
                20,
                8,
                0,
                tzinfo=timezone.utc,
            ),
            ended_at=datetime(
                2026,
                8,
                20,
                12,
                0,
                tzinfo=timezone.utc,
            ),
            status="invalid-status",
            total_quantity=100,
            good_quantity=90,
            reject_quantity=10,
            ideal_cycle_time_seconds=10.0,
        )

        db.add(production_run)

        with pytest.raises(IntegrityError):
            await db.commit()

        await db.rollback()


async def test_database_rejects_invalid_downtime_category(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    production_run = await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        hierarchy["production_line_id"],
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T12:00:00Z",
        ideal_cycle_time_seconds=10.0,
        total_quantity=500,
        good_quantity=480,
    )

    async with AsyncSessionLocal() as db:
        downtime_event = DowntimeEvent(
            production_run_id=production_run["id"],
            machine_id=hierarchy["machine_id"],
            category="invalid-category",
            reason="Database integrity test",
            started_at=datetime(
                2026,
                8,
                20,
                9,
                0,
                tzinfo=timezone.utc,
            ),
            ended_at=datetime(
                2026,
                8,
                20,
                10,
                0,
                tzinfo=timezone.utc,
            ),
        )

        db.add(downtime_event)

        with pytest.raises(IntegrityError) as exc_info:
            await db.commit()

        await db.rollback()

    assert (
        "ck_downtime_events_category"
        in str(exc_info.value)
    )


async def test_database_rejects_invalid_downtime_time_order(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    production_run = await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        hierarchy["production_line_id"],
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T12:00:00Z",
        ideal_cycle_time_seconds=10.0,
        total_quantity=500,
        good_quantity=480,
    )

    async with AsyncSessionLocal() as db:
        downtime_event = DowntimeEvent(
            production_run_id=production_run["id"],
            machine_id=hierarchy["machine_id"],
            category="unplanned",
            reason="Database integrity test",
            started_at=datetime(
                2026,
                8,
                20,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            ended_at=datetime(
                2026,
                8,
                20,
                9,
                0,
                tzinfo=timezone.utc,
            ),
        )

        db.add(downtime_event)

        with pytest.raises(IntegrityError) as exc_info:
            await db.commit()

        await db.rollback()

    assert (
        "ck_downtime_events_time_order"
        in str(exc_info.value)
    )



async def test_machine_reliability_service_filters_failure_events(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]
    machine_id = hierarchy["machine_id"]

    completed_run = await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T12:00:00Z",
        ideal_cycle_time_seconds=10.0,
        total_quantity=500,
        good_quantity=480,
    )

    # Valid machine failure: included.
    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        completed_run["id"],
        reason="Motor Failure",
        category="unplanned",
        started_at="2026-08-20T08:30:00Z",
        ended_at="2026-08-20T09:00:00Z",
        machine_id=machine_id,
    )

    # Planned downtime: excluded.
    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        completed_run["id"],
        reason="Preventive Maintenance",
        category="planned",
        started_at="2026-08-20T09:15:00Z",
        ended_at="2026-08-20T09:45:00Z",
        machine_id=machine_id,
    )

    # Line-wide downtime: excluded.
    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        completed_run["id"],
        reason="Material Shortage",
        category="unplanned",
        started_at="2026-08-20T10:00:00Z",
        ended_at="2026-08-20T10:30:00Z",
        machine_id=None,
    )

    # Another machine on the same production line: excluded.
    other_machine_response = await client.post(
        "/machines",
        headers=auth_headers["admin"],
        json={
            "area_id": hierarchy["area_id"],
            "production_line_id": line_id,
            "name": "Assembly Machine B",
            "code": "MACHINE-B",
            "location": "Assembly Line A",
            "status": "active",
        },
    )

    assert other_machine_response.status_code == 201

    other_machine_id = other_machine_response.json()["id"]

    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        completed_run["id"],
        reason="Other Machine Failure",
        category="unplanned",
        started_at="2026-08-20T10:30:00Z",
        ended_at="2026-08-20T11:30:00Z",
        machine_id=other_machine_id,
    )

    # Open machine failure: excluded.
    running_response = await client.post(
        "/production-runs",
        headers=auth_headers["admin"],
        json={
            "production_line_id": line_id,
            "started_at": "2026-08-20T13:00:00Z",
            "status": "running",
            "total_quantity": 0,
            "good_quantity": 0,
            "reject_quantity": 0,
            "ideal_cycle_time_seconds": 10.0,
        },
    )

    assert running_response.status_code == 201

    open_downtime_response = await client.post(
        "/downtime-events",
        headers=auth_headers["admin"],
        json={
            "production_run_id": running_response.json()["id"],
            "machine_id": machine_id,
            "category": "unplanned",
            "reason": "Open Failure",
            "started_at": "2026-08-20T13:30:00Z",
            "ended_at": None,
            "notes": None,
        },
    )

    assert open_downtime_response.status_code == 201

    async with AsyncSessionLocal() as db:
        metrics = await calculate_machine_reliability(
            db,
            machine_id,
        )

    assert metrics.failure_count == 1
    assert metrics.total_failure_downtime_seconds == pytest.approx(
        1800
    )
    assert metrics.mttr_seconds == pytest.approx(
        1800
    )


async def test_machine_reliability_service_filters_by_date_range(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]
    machine_id = hierarchy["machine_id"]

    first_run = await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T12:00:00Z",
        ideal_cycle_time_seconds=10.0,
        total_quantity=300,
        good_quantity=290,
    )

    second_run = await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-21T08:00:00Z",
        ended_at="2026-08-21T12:00:00Z",
        ideal_cycle_time_seconds=10.0,
        total_quantity=400,
        good_quantity=390,
    )

    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        first_run["id"],
        reason="Old Failure",
        category="unplanned",
        started_at="2026-08-20T09:00:00Z",
        ended_at="2026-08-20T10:00:00Z",
        machine_id=machine_id,
    )

    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        second_run["id"],
        reason="Selected Failure",
        category="unplanned",
        started_at="2026-08-21T09:00:00Z",
        ended_at="2026-08-21T11:00:00Z",
        machine_id=machine_id,
    )

    async with AsyncSessionLocal() as db:
        metrics = await calculate_machine_reliability(
            db,
            machine_id,
            start_at=datetime(
                2026,
                8,
                21,
                0,
                0,
                tzinfo=timezone.utc,
            ),
            end_at=datetime(
                2026,
                8,
                22,
                0,
                0,
                tzinfo=timezone.utc,
            ),
        )

    assert metrics.failure_count == 1
    assert metrics.total_failure_downtime_seconds == pytest.approx(
        7200
    )
    assert metrics.mttr_seconds == pytest.approx(
        7200
    )


async def test_machine_reliability_service_supports_zero_failures(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    async with AsyncSessionLocal() as db:
        metrics = await calculate_machine_reliability(
            db,
            hierarchy["machine_id"],
        )

    assert metrics.failure_count == 0
    assert metrics.total_failure_downtime_seconds == 0.0
    assert metrics.mttr_seconds is None


async def test_machine_reliability_service_rejects_invalid_date_range(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    async with AsyncSessionLocal() as db:
        with pytest.raises(
            MachineReliabilityServiceError,
            match="end_at must be later than start_at",
        ):
            await calculate_machine_reliability(
                db,
                hierarchy["machine_id"],
                start_at=datetime(
                    2026,
                    8,
                    22,
                    0,
                    0,
                    tzinfo=timezone.utc,
                ),
                end_at=datetime(
                    2026,
                    8,
                    21,
                    0,
                    0,
                    tzinfo=timezone.utc,
                ),
            )


async def test_machine_reliability_api_returns_failure_metrics(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]
    machine_id = hierarchy["machine_id"]

    production_run = await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T14:00:00Z",
        ideal_cycle_time_seconds=10.0,
        total_quantity=600,
        good_quantity=580,
    )

    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason="Motor Failure",
        category="unplanned",
        started_at="2026-08-20T09:00:00Z",
        ended_at="2026-08-20T09:30:00Z",
        machine_id=machine_id,
    )

    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason="Bearing Failure",
        category="unplanned",
        started_at="2026-08-20T11:00:00Z",
        ended_at="2026-08-20T12:30:00Z",
        machine_id=machine_id,
    )

    response = await client.get(
        f"/machines/{machine_id}/reliability",
        headers=auth_headers["admin"],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["machine_id"] == machine_id
    assert data["start_at"] is None
    assert data["end_at"] is None

    assert data["failure_count"] == 2

    # 30 minutes + 90 minutes = 120 minutes.
    assert data[
        "total_failure_downtime_seconds"
    ] == pytest.approx(
        7200
    )

    # MTTR = 120 minutes / 2 failures = 60 minutes.
    assert data["mttr_seconds"] == pytest.approx(
        3600
    )
    # Production run = 6 hours.
    # Failure downtime = 30m + 90m = 2 hours.
    # Operating exposure = 4 hours.
    assert data[
        "operating_exposure_seconds"
    ] == pytest.approx(
        4 * 3600
    )

    # 4 operating hours / 2 failures = 2 hours MTBF.
    assert data["mtbf_seconds"] == pytest.approx(
        2 * 3600
    )


async def test_machine_reliability_api_supports_zero_failures(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    response = await client.get(
        (
            f"/machines/"
            f"{hierarchy['machine_id']}/reliability"
        ),
        headers=auth_headers["admin"],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["failure_count"] == 0
    assert data["total_failure_downtime_seconds"] == 0.0
    assert data["mttr_seconds"] is None
    assert data["operating_exposure_seconds"] == 0.0
    assert data["mtbf_seconds"] is None


async def test_machine_reliability_api_filters_by_date_range(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]
    machine_id = hierarchy["machine_id"]

    first_run = await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T12:00:00Z",
        ideal_cycle_time_seconds=10.0,
        total_quantity=300,
        good_quantity=290,
    )

    second_run = await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-21T08:00:00Z",
        ended_at="2026-08-21T14:00:00Z",
        ideal_cycle_time_seconds=10.0,
        total_quantity=500,
        good_quantity=480,
    )

    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        first_run["id"],
        reason="Old Failure",
        category="unplanned",
        started_at="2026-08-20T09:00:00Z",
        ended_at="2026-08-20T10:00:00Z",
        machine_id=machine_id,
    )

    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        second_run["id"],
        reason="Selected Failure",
        category="unplanned",
        started_at="2026-08-21T10:00:00Z",
        ended_at="2026-08-21T12:00:00Z",
        machine_id=machine_id,
    )

    response = await client.get(
        f"/machines/{machine_id}/reliability",
        headers=auth_headers["admin"],
        params={
            "start_at": "2026-08-21T00:00:00Z",
            "end_at": "2026-08-22T00:00:00Z",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["failure_count"] == 1

    assert data[
        "total_failure_downtime_seconds"
    ] == pytest.approx(
        7200
    )

    assert data["mttr_seconds"] == pytest.approx(
        7200
    )

    assert data["start_at"] is not None
    assert data["end_at"] is not None
    # Only the selected 6-hour run is included.
    # Its failure lasts 2 hours.
    assert data[
        "operating_exposure_seconds"
    ] == pytest.approx(
        4 * 3600
    )

    assert data["mtbf_seconds"] == pytest.approx(
        4 * 3600
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
async def test_all_roles_can_read_machine_reliability_api(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
    role_name: str,
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    response = await client.get(
        (
            f"/machines/"
            f"{hierarchy['machine_id']}/reliability"
        ),
        headers=auth_headers[role_name],
    )

    assert response.status_code == 200


async def test_machine_reliability_api_returns_404_for_missing_machine(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    response = await client.get(
        "/machines/999999/reliability",
        headers=auth_headers["admin"],
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Machine not found"
    }


async def test_machine_reliability_api_rejects_invalid_date_range(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    response = await client.get(
        (
            f"/machines/"
            f"{hierarchy['machine_id']}/reliability"
        ),
        headers=auth_headers["admin"],
        params={
            "start_at": "2026-08-22T00:00:00Z",
            "end_at": "2026-08-21T00:00:00Z",
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": "end_at must be later than start_at"
    }

async def test_machine_reliability_service_calculates_mtbf(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]
    machine_id = hierarchy["machine_id"]

    production_run = await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T16:00:00Z",
        ideal_cycle_time_seconds=10.0,
        total_quantity=800,
        good_quantity=780,
    )

    # Target-machine failure: 1 hour.
    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason="Motor Failure",
        category="unplanned",
        started_at="2026-08-20T09:00:00Z",
        ended_at="2026-08-20T10:00:00Z",
        machine_id=machine_id,
    )

    # Planned line-wide downtime: another 1 hour.
    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason="Changeover",
        category="planned",
        started_at="2026-08-20T12:00:00Z",
        ended_at="2026-08-20T13:00:00Z",
        machine_id=None,
    )

    async with AsyncSessionLocal() as db:
        metrics = await calculate_machine_reliability(
            db,
            machine_id,
        )

    assert metrics.failure_count == 1

    assert metrics.total_failure_downtime_seconds == pytest.approx(
        3600
    )

    assert metrics.mttr_seconds == pytest.approx(
        3600
    )

    # Scheduled production exposure = 8 hours.
    # Unique downtime = 2 hours.
    # Operating exposure = 6 hours.
    assert metrics.operating_exposure_seconds == pytest.approx(
        6 * 3600
    )

    # One machine failure across 6 operating hours.
    assert metrics.mtbf_seconds == pytest.approx(
        6 * 3600
    )


async def test_machine_reliability_service_merges_overlapping_downtime_for_mtbf(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]
    machine_id = hierarchy["machine_id"]

    production_run = await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T12:00:00Z",
        ideal_cycle_time_seconds=10.0,
        total_quantity=400,
        good_quantity=390,
    )

    # Failure: 09:00 → 10:00.
    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason="Motor Failure",
        category="unplanned",
        started_at="2026-08-20T09:00:00Z",
        ended_at="2026-08-20T10:00:00Z",
        machine_id=machine_id,
    )

    # Overlapping planned downtime: 09:30 → 10:30.
    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason="Line Inspection",
        category="planned",
        started_at="2026-08-20T09:30:00Z",
        ended_at="2026-08-20T10:30:00Z",
        machine_id=None,
    )

    async with AsyncSessionLocal() as db:
        metrics = await calculate_machine_reliability(
            db,
            machine_id,
        )

    assert metrics.failure_count == 1

    # Recorded events total 2 hours, but unique elapsed
    # downtime is only 1.5 hours.
    #
    # 4h scheduled - 1.5h unique downtime = 2.5h exposure.
    assert metrics.operating_exposure_seconds == pytest.approx(
        2.5 * 3600
    )

    assert metrics.mtbf_seconds == pytest.approx(
        2.5 * 3600
    )


async def test_machine_reliability_service_returns_no_mtbf_without_failures(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]
    machine_id = hierarchy["machine_id"]

    await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T12:00:00Z",
        ideal_cycle_time_seconds=10.0,
        total_quantity=400,
        good_quantity=395,
    )

    async with AsyncSessionLocal() as db:
        metrics = await calculate_machine_reliability(
            db,
            machine_id,
        )

    assert metrics.failure_count == 0

    assert metrics.operating_exposure_seconds == pytest.approx(
        4 * 3600
    )

    assert metrics.mttr_seconds is None
    assert metrics.mtbf_seconds is None


async def test_machine_reliability_api_returns_no_mtbf_for_standalone_machine(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    standalone_machine_response = await client.post(
        "/machines",
        headers=auth_headers["admin"],
        json={
            "area_id": hierarchy["area_id"],
            "production_line_id": None,
            "name": "Standalone Utility Machine",
            "code": "STANDALONE-MACHINE",
            "location": "Utility Area",
            "status": "active",
        },
    )

    assert standalone_machine_response.status_code == 201

    machine_id = standalone_machine_response.json()["id"]

    response = await client.get(
        f"/machines/{machine_id}/reliability",
        headers=auth_headers["admin"],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["machine_id"] == machine_id
    assert data["failure_count"] == 0
    assert data["total_failure_downtime_seconds"] == 0.0
    assert data["mttr_seconds"] is None

    assert data["operating_exposure_seconds"] is None
    assert data["mtbf_seconds"] is None





async def test_operational_intelligence_service_combines_line_and_machine_metrics(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]
    machine_a_id = hierarchy["machine_id"]

    machine_b_response = await client.post(
        "/machines",
        headers=auth_headers["admin"],
        json={
            "area_id": hierarchy["area_id"],
            "production_line_id": line_id,
            "name": "Assembly Machine B",
            "code": "MACHINE-B",
            "location": "Assembly Line A",
            "status": "active",
        },
    )

    assert machine_b_response.status_code == 201
    machine_b_id = machine_b_response.json()["id"]

    production_run = await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T16:00:00Z",
        ideal_cycle_time_seconds=30.0,
        total_quantity=600,
        good_quantity=570,
    )

    # Machine A failure #1: 1 hour.
    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason="Machine A Motor Failure",
        category="unplanned",
        started_at="2026-08-20T09:00:00Z",
        ended_at="2026-08-20T10:00:00Z",
        machine_id=machine_a_id,
    )

    # Machine B failure: overlaps Machine A by 30 minutes.
    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason="Machine B Bearing Failure",
        category="unplanned",
        started_at="2026-08-20T09:30:00Z",
        ended_at="2026-08-20T10:30:00Z",
        machine_id=machine_b_id,
    )

    # Line-wide planned downtime: 1 hour.
    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason="Changeover",
        category="planned",
        started_at="2026-08-20T12:00:00Z",
        ended_at="2026-08-20T13:00:00Z",
        machine_id=None,
    )

    # Machine A failure #2: 30 minutes.
    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason="Machine A Sensor Failure",
        category="unplanned",
        started_at="2026-08-20T14:00:00Z",
        ended_at="2026-08-20T14:30:00Z",
        machine_id=machine_a_id,
    )

    async with AsyncSessionLocal() as db:
        result = (
            await calculate_production_line_operational_intelligence(
                db,
                line_id,
            )
        )

    assert result.production_line_id == line_id
    assert result.run_count == 1

    # -----------------------------------------------------
    # OEE uses UNIQUE elapsed downtime.
    #
    # Scheduled time = 8h
    # Planned downtime = 1h
    # Planned production time = 7h
    #
    # Unique unplanned downtime:
    # 09:00 -> 10:30 = 1.5h
    # 14:00 -> 14:30 = 0.5h
    # Total = 2h
    #
    # Operating time = 7h - 2h = 5h
    # -----------------------------------------------------

    assert result.oee.scheduled_time_seconds == pytest.approx(
        8 * 3600
    )

    assert result.oee.planned_downtime_seconds == pytest.approx(
        1 * 3600
    )

    assert result.oee.unplanned_downtime_seconds == pytest.approx(
        2 * 3600
    )

    assert result.oee.operating_time_seconds == pytest.approx(
        5 * 3600
    )

    assert result.oee.availability == pytest.approx(
        5 / 7
    )

        # -----------------------------------------------------
    # Operational priority ranking
    #
    # Machine A:
    # downtime rank = 1
    # failure rank = 1
    # MTTR rank = 2
    # MTBF rank = 1
    #
    # Aggregate rank value = 5
    #
    # Machine B:
    # downtime rank = 2
    # failure rank = 2
    # MTTR rank = 1
    # MTBF rank = 2
    #
    # Aggregate rank value = 7
    #
    # Therefore Machine A is priority #1.
    # -----------------------------------------------------

    priority = result.priority

    assert priority.top_priority_machine_id == machine_a_id

    assert len(priority.machines) == 2

    priority_a = next(
        machine
        for machine in priority.machines
        if machine.machine_id == machine_a_id
    )

    priority_b = next(
        machine
        for machine in priority.machines
        if machine.machine_id == machine_b_id
    )

    assert priority_a.priority_rank == 1
    assert priority_a.downtime_rank == 1
    assert priority_a.failure_rank == 1
    assert priority_a.mttr_rank == 2
    assert priority_a.mtbf_rank == 1

    assert priority_b.priority_rank == 2
    assert priority_b.downtime_rank == 2
    assert priority_b.failure_rank == 2
    assert priority_b.mttr_rank == 1
    assert priority_b.mtbf_rank == 2


    # ideal production time:
    # 600 units * 30 sec = 18,000 sec = 5h
    #
    # operating time is also 5h.
    assert result.oee.performance == pytest.approx(
        1.0
    )

    assert result.oee.quality == pytest.approx(
        570 / 600
    )

    assert result.oee.oee == pytest.approx(
        (5 / 7) * 1.0 * (570 / 600)
    )

    # -----------------------------------------------------
    # Downtime analytics uses RECORDED event duration.
    #
    # Machine A = 1h + 0.5h = 1.5h
    # Machine B = 1h
    # Line-wide = 1h
    #
    # Recorded burden = 3.5h
    # -----------------------------------------------------

    assert (
        result.operational_impact.recorded_downtime_seconds
        == pytest.approx(3.5 * 3600)
    )

    assert (
        result.operational_impact
        .machine_attributed_recorded_downtime_seconds
        == pytest.approx(2.5 * 3600)
    )

    assert (
        result.operational_impact
        .unattributed_recorded_downtime_seconds
        == pytest.approx(1 * 3600)
    )

    assert (
        result.operational_impact.machine_attributed_share
        == pytest.approx(2.5 / 3.5)
    )

    assert (
        result.operational_impact.unattributed_share
        == pytest.approx(1 / 3.5)
    )

    assert (
        result.operational_impact.top_downtime_machine_id
        == machine_a_id
    )

    # Machine A ranks first because it has 1.5h
    # of recorded downtime burden.
    machine_a = result.operational_impact.machines[0]
    machine_b = result.operational_impact.machines[1]

    assert machine_a.machine_id == machine_a_id

    assert machine_a.recorded_downtime_event_count == 2

    assert machine_a.recorded_downtime_seconds == pytest.approx(
        1.5 * 3600
    )

    assert machine_a.recorded_downtime_share == pytest.approx(
        1.5 / 3.5
    )

    assert machine_a.failure_count == 2

    # 90 minutes of failures / 2 failures.
    assert machine_a.mttr_seconds == pytest.approx(
        45 * 60
    )

    # All unique downtime across the run:
    # 1h planned + 2h unplanned = 3h.
    #
    # 8h - 3h = 5h operating exposure.
    assert machine_a.operating_exposure_seconds == pytest.approx(
        5 * 3600
    )

    # 5h exposure / 2 failures.
    assert machine_a.mtbf_seconds == pytest.approx(
        2.5 * 3600
    )

    assert machine_b.machine_id == machine_b_id

    assert machine_b.recorded_downtime_event_count == 1

    assert machine_b.recorded_downtime_seconds == pytest.approx(
        1 * 3600
    )

    assert machine_b.recorded_downtime_share == pytest.approx(
        1 / 3.5
    )

    assert machine_b.failure_count == 1

    assert machine_b.mttr_seconds == pytest.approx(
        1 * 3600
    )

    assert machine_b.operating_exposure_seconds == pytest.approx(
        5 * 3600
    )

    assert machine_b.mtbf_seconds == pytest.approx(
        5 * 3600
    )


async def test_operational_intelligence_service_includes_machine_without_downtime(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]

    machine_b_response = await client.post(
        "/machines",
        headers=auth_headers["admin"],
        json={
            "area_id": hierarchy["area_id"],
            "production_line_id": line_id,
            "name": "Healthy Machine B",
            "code": "HEALTHY-MACHINE-B",
            "location": "Assembly Line A",
            "status": "active",
        },
    )

    assert machine_b_response.status_code == 201
    machine_b_id = machine_b_response.json()["id"]

    production_run = await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T12:00:00Z",
        ideal_cycle_time_seconds=30.0,
        total_quantity=400,
        good_quantity=390,
    )

    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason="Machine A Failure",
        category="unplanned",
        started_at="2026-08-20T09:00:00Z",
        ended_at="2026-08-20T10:00:00Z",
        machine_id=hierarchy["machine_id"],
    )

    async with AsyncSessionLocal() as db:
        result = (
            await calculate_production_line_operational_intelligence(
                db,
                line_id,
            )
        )

    machine_b = next(
        machine
        for machine in result.operational_impact.machines
        if machine.machine_id == machine_b_id
    )

    assert machine_b.recorded_downtime_event_count == 0
    assert machine_b.recorded_downtime_seconds == 0.0
    assert machine_b.recorded_downtime_share == pytest.approx(0.0)

    assert machine_b.failure_count == 0
    assert machine_b.mttr_seconds is None

    # The machine still receives the line's production
    # operating exposure.
    assert machine_b.operating_exposure_seconds == pytest.approx(
        3 * 3600
    )

    assert machine_b.mtbf_seconds is None

    priority_healthy = next(
        machine
        for machine in result.priority.machines
        if machine.machine_id == machine_b_id
    )

    priority_failed = next(
        machine
        for machine in result.priority.machines
        if machine.machine_id == hierarchy["machine_id"]
    )

    assert (
        result.priority.top_priority_machine_id
        == hierarchy["machine_id"]
    )

    assert priority_failed.priority_rank == 1

    assert priority_healthy.priority_rank == 2
    assert priority_healthy.mttr_rank is None
    assert priority_healthy.mtbf_rank is None


async def test_operational_intelligence_service_rejects_invalid_date_range(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    async with AsyncSessionLocal() as db:
        with pytest.raises(
            OperationalIntelligenceServiceError,
            match="end_at must be later than start_at",
        ):
            await calculate_production_line_operational_intelligence(
                db,
                hierarchy["production_line_id"],
                start_at=datetime(
                    2026,
                    8,
                    20,
                    tzinfo=timezone.utc,
                ),
                end_at=datetime(
                    2026,
                    8,
                    10,
                    tzinfo=timezone.utc,
                ),
            )


async def test_operational_intelligence_api_returns_complete_report(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]
    machine_a_id = hierarchy["machine_id"]

    machine_b_response = await client.post(
        "/machines",
        headers=auth_headers["admin"],
        json={
            "area_id": hierarchy["area_id"],
            "production_line_id": line_id,
            "name": "Operational Machine B",
            "code": "OP-MACHINE-B",
            "location": "Operational Line",
            "status": "active",
        },
    )

    assert machine_b_response.status_code == 201
    machine_b_id = machine_b_response.json()["id"]

    production_run = await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T16:00:00Z",
        ideal_cycle_time_seconds=30.0,
        total_quantity=600,
        good_quantity=570,
    )

    # Machine A: 1 hour.
    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason="Motor Failure",
        category="unplanned",
        started_at="2026-08-20T09:00:00Z",
        ended_at="2026-08-20T10:00:00Z",
        machine_id=machine_a_id,
    )

    # Machine B: 1 hour, overlapping A by 30 minutes.
    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason="Bearing Failure",
        category="unplanned",
        started_at="2026-08-20T09:30:00Z",
        ended_at="2026-08-20T10:30:00Z",
        machine_id=machine_b_id,
    )

    # Line-wide planned event: 1 hour.
    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason="Changeover",
        category="planned",
        started_at="2026-08-20T12:00:00Z",
        ended_at="2026-08-20T13:00:00Z",
        machine_id=None,
    )

    # Second Machine A failure: 30 minutes.
    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason="Sensor Failure",
        category="unplanned",
        started_at="2026-08-20T14:00:00Z",
        ended_at="2026-08-20T14:30:00Z",
        machine_id=machine_a_id,
    )

    response = await client.get(
        f"/production-lines/{line_id}/operational-intelligence",
        headers=auth_headers["admin"],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["production_line_id"] == line_id
    assert data["run_count"] == 1
    assert data["start_at"] is None
    assert data["end_at"] is None

    # -----------------------------------------------------
    # OEE
    # -----------------------------------------------------

    oee = data["oee"]

    assert oee["run_count"] == 1

    assert oee["scheduled_time_seconds"] == pytest.approx(
        8 * 3600
    )

    assert oee["planned_downtime_seconds"] == pytest.approx(
        1 * 3600
    )

    assert oee["planned_production_time_seconds"] == pytest.approx(
        7 * 3600
    )

    assert oee["unplanned_downtime_seconds"] == pytest.approx(
        2 * 3600
    )

    assert oee["operating_time_seconds"] == pytest.approx(
        5 * 3600
    )

    assert oee["availability"] == pytest.approx(
        5 / 7
    )

    assert oee["performance"] == pytest.approx(
        1.0
    )

    assert oee["quality"] == pytest.approx(
        570 / 600
    )

    assert oee["oee"] == pytest.approx(
        (5 / 7) * (570 / 600)
    )

    # -----------------------------------------------------
    # Recorded downtime attribution
    # -----------------------------------------------------

    impact = data["operational_impact"]

    assert impact["recorded_downtime_seconds"] == pytest.approx(
        3.5 * 3600
    )

    assert (
        impact[
            "machine_attributed_recorded_downtime_seconds"
        ]
        == pytest.approx(2.5 * 3600)
    )

    assert (
        impact["unattributed_recorded_downtime_seconds"]
        == pytest.approx(1 * 3600)
    )

    assert impact["machine_attributed_share"] == pytest.approx(
        2.5 / 3.5
    )

    assert impact["unattributed_share"] == pytest.approx(
        1 / 3.5
    )

    assert impact["top_downtime_machine_id"] == machine_a_id

    # -----------------------------------------------------
    # Machine ranking + reliability
    # -----------------------------------------------------

    machines = impact["machines"]

    assert len(machines) == 2

    machine_a = machines[0]
    machine_b = machines[1]

    assert machine_a["machine_id"] == machine_a_id
    assert machine_a["recorded_downtime_event_count"] == 2

    assert machine_a["recorded_downtime_seconds"] == pytest.approx(
        1.5 * 3600
    )

    assert machine_a["recorded_downtime_share"] == pytest.approx(
        1.5 / 3.5
    )

    assert machine_a["failure_count"] == 2

    assert machine_a["mttr_seconds"] == pytest.approx(
        45 * 60
    )

    assert machine_a["operating_exposure_seconds"] == pytest.approx(
        5 * 3600
    )

    assert machine_a["mtbf_seconds"] == pytest.approx(
        2.5 * 3600
    )

    assert machine_b["machine_id"] == machine_b_id
    assert machine_b["recorded_downtime_event_count"] == 1

    assert machine_b["recorded_downtime_seconds"] == pytest.approx(
        1 * 3600
    )

    assert machine_b["failure_count"] == 1

    assert machine_b["mttr_seconds"] == pytest.approx(
        1 * 3600
    )

    assert machine_b["mtbf_seconds"] == pytest.approx(
        5 * 3600
    )

    # -----------------------------------------------------
    # Explainable operational priority
    # -----------------------------------------------------

    priority = data["priority"]

    assert priority["top_priority_machine_id"] == machine_a_id

    assert len(priority["machines"]) == 2

    priority_a = next(
        machine
        for machine in priority["machines"]
        if machine["machine_id"] == machine_a_id
    )

    priority_b = next(
        machine
        for machine in priority["machines"]
        if machine["machine_id"] == machine_b_id
    )

    assert priority_a["priority_rank"] == 1
    assert priority_a["downtime_rank"] == 1
    assert priority_a["failure_rank"] == 1
    assert priority_a["mttr_rank"] == 2
    assert priority_a["mtbf_rank"] == 1

    assert priority_b["priority_rank"] == 2
    assert priority_b["downtime_rank"] == 2
    assert priority_b["failure_rank"] == 2
    assert priority_b["mttr_rank"] == 1
    assert priority_b["mtbf_rank"] == 2


async def test_operational_intelligence_api_allows_all_authenticated_roles(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]

    await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T12:00:00Z",
        ideal_cycle_time_seconds=30.0,
        total_quantity=300,
        good_quantity=290,
    )

    for role in (
        "admin",
        "manager",
        "technician",
        "operator",
    ):
        response = await client.get(
            (
                f"/production-lines/{line_id}"
                "/operational-intelligence"
            ),
            headers=auth_headers[role],
        )

        assert response.status_code == 200


async def test_operational_intelligence_api_returns_404_for_missing_line(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    response = await client.get(
        "/production-lines/999999/operational-intelligence",
        headers=auth_headers["admin"],
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Production line not found"
    )


async def test_operational_intelligence_api_rejects_invalid_date_range(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    response = await client.get(
        (
            f"/production-lines/"
            f"{hierarchy['production_line_id']}"
            "/operational-intelligence"
        ),
        headers=auth_headers["admin"],
        params={
            "start_at": "2026-08-20T16:00:00Z",
            "end_at": "2026-08-20T08:00:00Z",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "end_at must be later than start_at"
    )


async def test_operational_intelligence_api_rejects_period_without_completed_runs(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    response = await client.get(
        (
            f"/production-lines/"
            f"{hierarchy['production_line_id']}"
            "/operational-intelligence"
        ),
        headers=auth_headers["admin"],
    )

    assert response.status_code == 422

    assert response.json()["detail"] == (
        "No completed production runs found "
        "for the selected period"
    )

async def test_operational_intelligence_service_calculates_machine_downtime_reasons(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]
    machine_id = hierarchy["machine_id"]

    production_run = await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T16:00:00Z",
        ideal_cycle_time_seconds=30.0,
        total_quantity=500,
        good_quantity=480,
    )

    # -----------------------------------------------------
    # Motor Overheating:
    # 2 events
    # 2 hours total
    #
    # Bearing Failure:
    # 3 events
    # 1.5 hours total
    #
    # Therefore:
    # dominant duration reason = Motor Overheating
    # most frequent reason = Bearing Failure
    # -----------------------------------------------------

    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason="Motor Overheating",
        category="unplanned",
        started_at="2026-08-20T08:30:00Z",
        ended_at="2026-08-20T09:30:00Z",
        machine_id=machine_id,
    )

    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason=" motor overheating ",
        category="unplanned",
        started_at="2026-08-20T10:00:00Z",
        ended_at="2026-08-20T11:00:00Z",
        machine_id=machine_id,
    )

    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason="Bearing Failure",
        category="unplanned",
        started_at="2026-08-20T11:30:00Z",
        ended_at="2026-08-20T12:00:00Z",
        machine_id=machine_id,
    )

    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason="Bearing Failure",
        category="unplanned",
        started_at="2026-08-20T12:30:00Z",
        ended_at="2026-08-20T13:00:00Z",
        machine_id=machine_id,
    )

    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason="Bearing Failure",
        category="unplanned",
        started_at="2026-08-20T13:30:00Z",
        ended_at="2026-08-20T14:00:00Z",
        machine_id=machine_id,
    )

    async with AsyncSessionLocal() as db:
        result = (
            await calculate_production_line_operational_intelligence(
                db,
                line_id,
            )
        )

    assert len(result.downtime_reasons) == 1

    machine_reasons = result.downtime_reasons[0]

    assert machine_reasons.machine_id == machine_id
    assert machine_reasons.event_count == 5

    assert (
        machine_reasons.recorded_downtime_seconds
        == pytest.approx(3.5 * 3600)
    )

    assert (
        machine_reasons.dominant_duration_reason
        == "Motor Overheating"
    )

    assert (
        machine_reasons.most_frequent_reason
        == "Bearing Failure"
    )

    assert len(machine_reasons.by_reason) == 2

    motor = machine_reasons.by_reason[0]
    bearing = machine_reasons.by_reason[1]

    assert motor.reason == "Motor Overheating"
    assert motor.event_count == 2

    assert motor.duration_seconds == pytest.approx(
        2 * 3600
    )

    assert motor.percentage == pytest.approx(
        2 / 3.5
    )

    assert motor.unplanned_event_count == 2

    assert (
        motor.unplanned_duration_seconds
        == pytest.approx(2 * 3600)
    )

    assert bearing.reason == "Bearing Failure"
    assert bearing.event_count == 3

    assert bearing.duration_seconds == pytest.approx(
        1.5 * 3600
    )

    assert bearing.percentage == pytest.approx(
        1.5 / 3.5
    )

    assert bearing.unplanned_event_count == 3


async def test_operational_intelligence_api_returns_machine_downtime_reasons(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    hierarchy = await create_production_test_hierarchy(
        client,
        auth_headers["admin"],
    )

    line_id = hierarchy["production_line_id"]
    machine_id = hierarchy["machine_id"]

    production_run = await create_completed_line_analytics_run(
        client,
        auth_headers["admin"],
        line_id,
        started_at="2026-08-20T08:00:00Z",
        ended_at="2026-08-20T16:00:00Z",
        ideal_cycle_time_seconds=30.0,
        total_quantity=500,
        good_quantity=480,
    )

    # Motor Overheating:
    # 2 events
    # 2 hours total
    #
    # Bearing Failure:
    # 3 events
    # 1.5 hours total
    #
    # Duration leader != frequency leader.

    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason="Motor Overheating",
        category="unplanned",
        started_at="2026-08-20T08:30:00Z",
        ended_at="2026-08-20T09:30:00Z",
        machine_id=machine_id,
    )

    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason=" motor overheating ",
        category="unplanned",
        started_at="2026-08-20T10:00:00Z",
        ended_at="2026-08-20T11:00:00Z",
        machine_id=machine_id,
    )

    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason="Bearing Failure",
        category="unplanned",
        started_at="2026-08-20T11:30:00Z",
        ended_at="2026-08-20T12:00:00Z",
        machine_id=machine_id,
    )

    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason="Bearing Failure",
        category="unplanned",
        started_at="2026-08-20T12:30:00Z",
        ended_at="2026-08-20T13:00:00Z",
        machine_id=machine_id,
    )

    await create_line_analytics_downtime(
        client,
        auth_headers["admin"],
        production_run["id"],
        reason="Bearing Failure",
        category="unplanned",
        started_at="2026-08-20T13:30:00Z",
        ended_at="2026-08-20T14:00:00Z",
        machine_id=machine_id,
    )

    response = await client.get(
        (
            f"/production-lines/{line_id}"
            "/operational-intelligence"
        ),
        headers=auth_headers["admin"],
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["downtime_reasons"]) == 1

    machine_reasons = data["downtime_reasons"][0]

    assert machine_reasons["machine_id"] == machine_id
    assert machine_reasons["event_count"] == 5

    assert (
        machine_reasons["recorded_downtime_seconds"]
        == pytest.approx(3.5 * 3600)
    )

    assert (
        machine_reasons["dominant_duration_reason"]
        == "Motor Overheating"
    )

    assert (
        machine_reasons["most_frequent_reason"]
        == "Bearing Failure"
    )

    reasons = machine_reasons["by_reason"]

    assert len(reasons) == 2

    motor = reasons[0]
    bearing = reasons[1]

    assert motor["reason"] == "Motor Overheating"
    assert motor["event_count"] == 2

    assert motor["duration_seconds"] == pytest.approx(
        2 * 3600
    )

    assert motor["percentage"] == pytest.approx(
        2 / 3.5
    )

    assert motor["planned_event_count"] == 0
    assert motor["planned_duration_seconds"] == 0.0

    assert motor["unplanned_event_count"] == 2

    assert (
        motor["unplanned_duration_seconds"]
        == pytest.approx(2 * 3600)
    )

    assert bearing["reason"] == "Bearing Failure"
    assert bearing["event_count"] == 3

    assert bearing["duration_seconds"] == pytest.approx(
        1.5 * 3600
    )

    assert bearing["percentage"] == pytest.approx(
        1.5 / 3.5
    )

    assert bearing["unplanned_event_count"] == 3