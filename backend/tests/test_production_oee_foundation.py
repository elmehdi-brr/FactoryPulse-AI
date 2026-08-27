import pytest
from httpx import AsyncClient


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