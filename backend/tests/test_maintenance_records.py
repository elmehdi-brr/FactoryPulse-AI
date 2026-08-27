import pytest
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone

from app.services.maintenance_analytics_service import (
    MaintenanceAnalyticsServiceError,
    calculate_machine_maintenance_effectiveness,
)  

from app.db.session import AsyncSessionLocal
from app.models.maintenance_record import MaintenanceRecord


async def create_maintenance_test_machine(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> int:
    organization_response = await client.post(
        "/organizations",
        headers=admin_headers,
        json={
            "name": "Maintenance Test Organization",
            "code": "MAINT-ORG",
            "description": "Maintenance tests",
        },
    )

    assert organization_response.status_code == 201
    organization_id = organization_response.json()["id"]

    site_response = await client.post(
        "/sites",
        headers=admin_headers,
        json={
            "organization_id": organization_id,
            "name": "Maintenance Test Site",
            "code": "MAINT-SITE",
            "location": "Test",
            "description": "Maintenance test site",
        },
    )

    assert site_response.status_code == 201
    site_id = site_response.json()["id"]

    area_response = await client.post(
        "/areas",
        headers=admin_headers,
        json={
            "site_id": site_id,
            "name": "Maintenance Area",
            "code": "MAINT-AREA",
            "description": "Maintenance test area",
        },
    )

    assert area_response.status_code == 201
    area_id = area_response.json()["id"]

    machine_response = await client.post(
        "/machines",
        headers=admin_headers,
        json={
            "area_id": area_id,
            "production_line_id": None,
            "name": "Maintenance Machine",
            "code": "MAINT-MACHINE",
            "location": "Maintenance Area",
            "status": "active",
        },
    )

    assert machine_response.status_code == 201

    return machine_response.json()["id"]


async def create_valid_maintenance_record(
    client: AsyncClient,
    admin_headers: dict[str, str],
    machine_id: int,
) -> dict:
    response = await client.post(
        "/maintenance-records",
        headers=admin_headers,
        json={
            "machine_id": machine_id,
            "maintenance_type": "corrective",
            "description": "Motor repaired and verified",
            "status": "verified",
            "performed_at": "2026-08-20T10:00:00Z",
        },
    )

    assert response.status_code == 201

    return response.json()


async def test_create_valid_maintenance_record(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    machine_id = await create_maintenance_test_machine(
        client,
        auth_headers["admin"],
    )

    response = await client.post(
        "/maintenance-records",
        headers=auth_headers["admin"],
        json={
            "machine_id": machine_id,
            "maintenance_type": "corrective",
            "description": "Motor repaired",
            "status": "completed",
            "performed_at": "2026-08-20T10:00:00Z",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["machine_id"] == machine_id
    assert data["maintenance_type"] == "corrective"
    assert data["status"] == "completed"
    assert data["performed_at"] is not None


async def test_create_rejects_invalid_maintenance_type(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    machine_id = await create_maintenance_test_machine(
        client,
        auth_headers["admin"],
    )

    response = await client.post(
        "/maintenance-records",
        headers=auth_headers["admin"],
        json={
            "machine_id": machine_id,
            "maintenance_type": "inspection",
            "description": "Invalid type",
            "status": "planned",
        },
    )

    assert response.status_code == 422

    assert any(
        error["loc"][-1] == "maintenance_type"
        for error in response.json()["detail"]
    )


async def test_create_rejects_invalid_maintenance_status(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    machine_id = await create_maintenance_test_machine(
        client,
        auth_headers["admin"],
    )

    response = await client.post(
        "/maintenance-records",
        headers=auth_headers["admin"],
        json={
            "machine_id": machine_id,
            "maintenance_type": "preventive",
            "description": "Invalid status",
            "status": "unknown",
        },
    )

    assert response.status_code == 422

    assert any(
        error["loc"][-1] == "status"
        for error in response.json()["detail"]
    )


@pytest.mark.parametrize(
    ("payload", "field_name"),
    [
        (
            {"maintenance_type": "emergency"},
            "maintenance_type",
        ),
        (
            {"status": "done"},
            "status",
        ),
    ],
)
async def test_update_rejects_invalid_maintenance_vocabulary(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
    payload: dict[str, str],
    field_name: str,
) -> None:
    machine_id = await create_maintenance_test_machine(
        client,
        auth_headers["admin"],
    )

    record = await create_valid_maintenance_record(
        client,
        auth_headers["admin"],
        machine_id,
    )

    response = await client.patch(
        f"/maintenance-records/{record['id']}",
        headers=auth_headers["admin"],
        json=payload,
    )

    assert response.status_code == 422

    assert any(
        error["loc"][-1] == field_name
        for error in response.json()["detail"]
    )


async def test_create_returns_404_for_missing_machine(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    response = await client.post(
        "/maintenance-records",
        headers=auth_headers["admin"],
        json={
            "machine_id": 999999,
            "maintenance_type": "corrective",
            "description": "Missing machine",
            "status": "planned",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Machine not found"
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
async def test_all_roles_can_read_machine_maintenance_records(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
    role_name: str,
) -> None:
    machine_id = await create_maintenance_test_machine(
        client,
        auth_headers["admin"],
    )

    await create_valid_maintenance_record(
        client,
        auth_headers["admin"],
        machine_id,
    )

    response = await client.get(
        f"/machines/{machine_id}/maintenance-records",
        headers=auth_headers[role_name],
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["machine_id"] == machine_id


async def test_operator_cannot_create_maintenance_record(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    machine_id = await create_maintenance_test_machine(
        client,
        auth_headers["admin"],
    )

    response = await client.post(
        "/maintenance-records",
        headers=auth_headers["operator"],
        json={
            "machine_id": machine_id,
            "maintenance_type": "corrective",
            "description": "Unauthorized maintenance write",
            "status": "completed",
        },
    )

    assert response.status_code == 403


async def test_database_rejects_invalid_maintenance_type(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    machine_id = await create_maintenance_test_machine(
        client,
        auth_headers["admin"],
    )

    async with AsyncSessionLocal() as db:
        record = MaintenanceRecord(
            machine_id=machine_id,
            maintenance_type="inspection",
            description="Direct database constraint test",
            status="planned",
        )

        db.add(record)

        with pytest.raises(IntegrityError) as exc_info:
            await db.commit()

        await db.rollback()

    assert (
        "ck_maintenance_records_maintenance_type"
        in str(exc_info.value.orig)
    )


async def test_database_rejects_invalid_maintenance_status(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    machine_id = await create_maintenance_test_machine(
        client,
        auth_headers["admin"],
    )

    async with AsyncSessionLocal() as db:
        record = MaintenanceRecord(
            machine_id=machine_id,
            maintenance_type="preventive",
            description="Direct database constraint test",
            status="unknown",
        )

        db.add(record)

        with pytest.raises(IntegrityError) as exc_info:
            await db.commit()

        await db.rollback()

    assert (
        "ck_maintenance_records_status"
        in str(exc_info.value.orig)
    )


async def test_maintenance_analytics_service_calculates_metrics(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    machine_id = await create_maintenance_test_machine(
        client,
        auth_headers["admin"],
    )

    async with AsyncSessionLocal() as db:
        db.add_all(
            [
                MaintenanceRecord(
                    machine_id=machine_id,
                    maintenance_type="preventive",
                    description="Scheduled inspection",
                    status="completed",
                    performed_by_user_id=1,
                ),
                MaintenanceRecord(
                    machine_id=machine_id,
                    maintenance_type="corrective",
                    description="Motor repair",
                    status="verified",
                    alert_id=None,
                    performed_by_user_id=1,
                ),
                MaintenanceRecord(
                    machine_id=machine_id,
                    maintenance_type="preventive",
                    description="Future service",
                    status="planned",
                ),
                MaintenanceRecord(
                    machine_id=machine_id,
                    maintenance_type="corrective",
                    description="Cancelled repair",
                    status="cancelled",
                ),
            ]
        )

        await db.commit()

    async with AsyncSessionLocal() as db:
        metrics = await calculate_machine_maintenance_effectiveness(
            db,
            machine_id,
        )

    assert metrics.total_records == 4

    assert metrics.preventive_count == 2
    assert metrics.corrective_count == 2
    assert metrics.preventive_share == pytest.approx(0.5)

    assert metrics.planned_count == 1
    assert metrics.in_progress_count == 0
    assert metrics.completed_count == 1
    assert metrics.verified_count == 1
    assert metrics.cancelled_count == 1

    assert metrics.finished_count == 2
    assert metrics.completion_rate == pytest.approx(2 / 3)
    assert metrics.verification_rate == pytest.approx(0.5)

    assert metrics.assigned_count == 2
    assert metrics.assignment_rate == pytest.approx(0.5)


async def test_maintenance_analytics_service_isolates_machine_records(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    machine_id = await create_maintenance_test_machine(
        client,
        auth_headers["admin"],
    )

    machine_response = await client.get(
        f"/machines/{machine_id}",
        headers=auth_headers["admin"],
    )

    assert machine_response.status_code == 200

    area_id = machine_response.json()["area_id"]

    other_machine_response = await client.post(
        "/machines",
        headers=auth_headers["admin"],
        json={
            "area_id": area_id,
            "production_line_id": None,
            "name": "Other Maintenance Machine",
            "code": "OTHER-MAINT-MACHINE",
            "location": "Maintenance Area",
            "status": "active",
        },
    )

    assert other_machine_response.status_code == 201

    other_machine_id = other_machine_response.json()["id"]

    async with AsyncSessionLocal() as db:
        db.add_all(
            [
                MaintenanceRecord(
                    machine_id=machine_id,
                    maintenance_type="corrective",
                    description="Target machine repair",
                    status="completed",
                ),
                MaintenanceRecord(
                    machine_id=other_machine_id,
                    maintenance_type="preventive",
                    description="Other machine service",
                    status="verified",
                ),
            ]
        )

        await db.commit()

    async with AsyncSessionLocal() as db:
        metrics = await calculate_machine_maintenance_effectiveness(
            db,
            machine_id,
        )

    assert metrics.total_records == 1
    assert metrics.corrective_count == 1
    assert metrics.preventive_count == 0
    assert metrics.completed_count == 1
    assert metrics.verified_count == 0


async def test_maintenance_analytics_service_filters_by_created_at(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    machine_id = await create_maintenance_test_machine(
        client,
        auth_headers["admin"],
    )

    async with AsyncSessionLocal() as db:
        db.add_all(
            [
                MaintenanceRecord(
                    machine_id=machine_id,
                    maintenance_type="preventive",
                    description="Old maintenance",
                    status="completed",
                    created_at=datetime(
                        2026,
                        8,
                        1,
                        10,
                        0,
                        tzinfo=timezone.utc,
                    ),
                ),
                MaintenanceRecord(
                    machine_id=machine_id,
                    maintenance_type="corrective",
                    description="Selected maintenance",
                    status="verified",
                    created_at=datetime(
                        2026,
                        8,
                        10,
                        10,
                        0,
                        tzinfo=timezone.utc,
                    ),
                ),
                MaintenanceRecord(
                    machine_id=machine_id,
                    maintenance_type="preventive",
                    description="Future maintenance",
                    status="planned",
                    created_at=datetime(
                        2026,
                        8,
                        20,
                        10,
                        0,
                        tzinfo=timezone.utc,
                    ),
                ),
            ]
        )

        await db.commit()

    async with AsyncSessionLocal() as db:
        metrics = await calculate_machine_maintenance_effectiveness(
            db,
            machine_id,
            start_at=datetime(
                2026,
                8,
                5,
                tzinfo=timezone.utc,
            ),
            end_at=datetime(
                2026,
                8,
                15,
                tzinfo=timezone.utc,
            ),
        )

    assert metrics.total_records == 1
    assert metrics.corrective_count == 1
    assert metrics.preventive_count == 0
    assert metrics.verified_count == 1
    assert metrics.finished_count == 1
    assert metrics.completion_rate == pytest.approx(1.0)
    assert metrics.verification_rate == pytest.approx(1.0)


async def test_maintenance_analytics_service_rejects_invalid_date_range(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    machine_id = await create_maintenance_test_machine(
        client,
        auth_headers["admin"],
    )

    async with AsyncSessionLocal() as db:
        with pytest.raises(
            MaintenanceAnalyticsServiceError,
            match="end_at must be later than start_at",
        ):
            await calculate_machine_maintenance_effectiveness(
                db,
                machine_id,
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

async def test_maintenance_analytics_api_returns_metrics(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    machine_id = await create_maintenance_test_machine(
        client,
        auth_headers["admin"],
    )

    async with AsyncSessionLocal() as db:
        db.add_all(
            [
                MaintenanceRecord(
                    machine_id=machine_id,
                    maintenance_type="preventive",
                    description="Scheduled service",
                    status="completed",
                    performed_by_user_id=1,
                ),
                MaintenanceRecord(
                    machine_id=machine_id,
                    maintenance_type="corrective",
                    description="Motor repair",
                    status="verified",
                    performed_by_user_id=1,
                ),
                MaintenanceRecord(
                    machine_id=machine_id,
                    maintenance_type="preventive",
                    description="Upcoming service",
                    status="planned",
                ),
                MaintenanceRecord(
                    machine_id=machine_id,
                    maintenance_type="corrective",
                    description="Cancelled intervention",
                    status="cancelled",
                ),
            ]
        )

        await db.commit()

    response = await client.get(
        f"/machines/{machine_id}/maintenance-analytics",
        headers=auth_headers["admin"],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["machine_id"] == machine_id
    assert data["start_at"] is None
    assert data["end_at"] is None

    assert data["total_records"] == 4

    assert data["preventive_count"] == 2
    assert data["corrective_count"] == 2
    assert data["preventive_share"] == pytest.approx(0.5)

    assert data["planned_count"] == 1
    assert data["in_progress_count"] == 0
    assert data["completed_count"] == 1
    assert data["verified_count"] == 1
    assert data["cancelled_count"] == 1

    assert data["finished_count"] == 2
    assert data["completion_rate"] == pytest.approx(2 / 3)
    assert data["verification_rate"] == pytest.approx(0.5)

    assert data["alert_linked_count"] == 0
    assert data["alert_link_rate"] == pytest.approx(0.0)

    assert data["assigned_count"] == 2
    assert data["assignment_rate"] == pytest.approx(0.5)


async def test_maintenance_analytics_api_supports_empty_history(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    machine_id = await create_maintenance_test_machine(
        client,
        auth_headers["admin"],
    )

    response = await client.get(
        f"/machines/{machine_id}/maintenance-analytics",
        headers=auth_headers["admin"],
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_records"] == 0

    assert data["preventive_count"] == 0
    assert data["corrective_count"] == 0

    assert data["planned_count"] == 0
    assert data["in_progress_count"] == 0
    assert data["completed_count"] == 0
    assert data["verified_count"] == 0
    assert data["cancelled_count"] == 0

    assert data["finished_count"] == 0

    assert data["preventive_share"] is None
    assert data["completion_rate"] is None
    assert data["verification_rate"] is None
    assert data["alert_link_rate"] is None
    assert data["assignment_rate"] is None


async def test_maintenance_analytics_api_filters_by_created_at(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    machine_id = await create_maintenance_test_machine(
        client,
        auth_headers["admin"],
    )

    async with AsyncSessionLocal() as db:
        db.add_all(
            [
                MaintenanceRecord(
                    machine_id=machine_id,
                    maintenance_type="preventive",
                    description="Old maintenance",
                    status="completed",
                    created_at=datetime(
                        2026,
                        8,
                        1,
                        10,
                        0,
                        tzinfo=timezone.utc,
                    ),
                ),
                MaintenanceRecord(
                    machine_id=machine_id,
                    maintenance_type="corrective",
                    description="Selected maintenance",
                    status="verified",
                    created_at=datetime(
                        2026,
                        8,
                        10,
                        10,
                        0,
                        tzinfo=timezone.utc,
                    ),
                ),
                MaintenanceRecord(
                    machine_id=machine_id,
                    maintenance_type="preventive",
                    description="Future maintenance",
                    status="planned",
                    created_at=datetime(
                        2026,
                        8,
                        20,
                        10,
                        0,
                        tzinfo=timezone.utc,
                    ),
                ),
            ]
        )

        await db.commit()

    response = await client.get(
        f"/machines/{machine_id}/maintenance-analytics",
        headers=auth_headers["admin"],
        params={
            "start_at": "2026-08-05T00:00:00Z",
            "end_at": "2026-08-15T00:00:00Z",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_records"] == 1
    assert data["corrective_count"] == 1
    assert data["preventive_count"] == 0
    assert data["verified_count"] == 1
    assert data["finished_count"] == 1

    assert data["completion_rate"] == pytest.approx(1.0)
    assert data["verification_rate"] == pytest.approx(1.0)

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
async def test_all_roles_can_read_maintenance_analytics_api(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
    role_name: str,
) -> None:
    machine_id = await create_maintenance_test_machine(
        client,
        auth_headers["admin"],
    )

    response = await client.get(
        f"/machines/{machine_id}/maintenance-analytics",
        headers=auth_headers[role_name],
    )

    assert response.status_code == 200


async def test_maintenance_analytics_api_returns_404_for_missing_machine(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    response = await client.get(
        "/machines/999999/maintenance-analytics",
        headers=auth_headers["admin"],
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Machine not found"
    }


async def test_maintenance_analytics_api_rejects_invalid_date_range(
    client: AsyncClient,
    auth_headers: dict[str, dict[str, str]],
) -> None:
    machine_id = await create_maintenance_test_machine(
        client,
        auth_headers["admin"],
    )

    response = await client.get(
        f"/machines/{machine_id}/maintenance-analytics",
        headers=auth_headers["admin"],
        params={
            "start_at": "2026-08-20T00:00:00Z",
            "end_at": "2026-08-10T00:00:00Z",
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": "end_at must be later than start_at"
    }