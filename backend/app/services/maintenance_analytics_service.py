from datetime import datetime
from app.models.alert import Alert
from app.models.sensor import Sensor

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.maintenance.analytics import (
    MaintenanceAnalyticsError,
    MaintenanceEffectivenessMetrics,
    MaintenanceRecordSnapshot,
    calculate_maintenance_effectiveness,
    MaintenanceResponseMetrics,
    MaintenanceResponseObservation,
    calculate_maintenance_response_metrics,
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

    

async def calculate_machine_maintenance_response(
    db: AsyncSession,
    machine_id: int,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> MaintenanceResponseMetrics:
    validate_maintenance_analytics_period(
        start_at,
        end_at,
    )

    alert_query = (
        select(Alert)
        .join(
            Sensor,
            Alert.sensor_id == Sensor.id,
        )
        .where(
            Sensor.machine_id == machine_id
        )
    )

    if start_at is not None:
        alert_query = alert_query.where(
            Alert.created_at >= start_at
        )

    if end_at is not None:
        alert_query = alert_query.where(
            Alert.created_at <= end_at
        )

    alert_query = alert_query.order_by(
        Alert.created_at,
        Alert.id,
    )

    alert_result = await db.execute(
        alert_query
    )

    alerts = list(
        alert_result.scalars().all()
    )

    if not alerts:
        return calculate_maintenance_response_metrics(
            []
        )

    alert_ids = [
        alert.id
        for alert in alerts
    ]

    maintenance_query = (
        select(MaintenanceRecord)
        .where(
            MaintenanceRecord.machine_id == machine_id,
            MaintenanceRecord.alert_id.in_(alert_ids),
            MaintenanceRecord.status.in_(
                [
                    "completed",
                    "verified",
                ]
            ),
            MaintenanceRecord.performed_at.is_not(None),
        )
        .order_by(
            MaintenanceRecord.alert_id,
            MaintenanceRecord.performed_at,
            MaintenanceRecord.id,
        )
    )

    maintenance_result = await db.execute(
        maintenance_query
    )

    maintenance_records = list(
        maintenance_result.scalars().all()
    )

    earliest_response_by_alert: dict[
        int,
        datetime,
    ] = {}

    for record in maintenance_records:
        if (
            record.alert_id is None
            or record.performed_at is None
        ):
            continue

        if record.alert_id not in earliest_response_by_alert:
            earliest_response_by_alert[
                record.alert_id
            ] = record.performed_at

    observations = [
        MaintenanceResponseObservation(
            alert_created_at=alert.created_at,
            maintenance_performed_at=(
                earliest_response_by_alert.get(
                    alert.id
                )
            ),
        )
        for alert in alerts
    ]

    try:
        return calculate_maintenance_response_metrics(
            observations
        )
    except MaintenanceAnalyticsError as exc:
        raise MaintenanceAnalyticsServiceError(
            str(exc)
        ) from exc