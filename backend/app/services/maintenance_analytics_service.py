from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.maintenance.analytics import (
    MaintenanceAnalyticsError,
    MaintenanceEffectivenessMetrics,
    MaintenanceRecordSnapshot,
    calculate_maintenance_effectiveness,
)
from app.models.maintenance_record import MaintenanceRecord


class MaintenanceAnalyticsServiceError(ValueError):
    pass


def validate_maintenance_analytics_period(
    start_at: datetime | None,
    end_at: datetime | None,
) -> None:
    if (
        start_at is not None
        and end_at is not None
        and end_at <= start_at
    ):
        raise MaintenanceAnalyticsServiceError(
            "end_at must be later than start_at"
        )


async def get_machine_maintenance_records_for_analytics(
    db: AsyncSession,
    machine_id: int,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> list[MaintenanceRecord]:
    validate_maintenance_analytics_period(
        start_at,
        end_at,
    )

    query = select(MaintenanceRecord).where(
        MaintenanceRecord.machine_id == machine_id
    )

    if start_at is not None:
        query = query.where(
            MaintenanceRecord.created_at >= start_at
        )

    if end_at is not None:
        query = query.where(
            MaintenanceRecord.created_at <= end_at
        )

    query = query.order_by(
        MaintenanceRecord.created_at,
        MaintenanceRecord.id,
    )

    result = await db.execute(query)

    return list(result.scalars().all())


async def calculate_machine_maintenance_effectiveness(
    db: AsyncSession,
    machine_id: int,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> MaintenanceEffectivenessMetrics:
    records = await get_machine_maintenance_records_for_analytics(
        db,
        machine_id,
        start_at=start_at,
        end_at=end_at,
    )

    snapshots = [
        MaintenanceRecordSnapshot(
            maintenance_type=record.maintenance_type,
            status=record.status,
            alert_id=record.alert_id,
            performed_by_user_id=(
                record.performed_by_user_id
            ),
        )
        for record in records
    ]

    try:
        return calculate_maintenance_effectiveness(
            snapshots
        )
    except MaintenanceAnalyticsError as exc:
        raise MaintenanceAnalyticsServiceError(
            str(exc)
        ) from exc