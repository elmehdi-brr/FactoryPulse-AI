from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.maintenance_record import MaintenanceRecord
from app.schemas.maintenance_record import (
    MaintenanceRecordCreate,
    MaintenanceRecordUpdate,
)


async def create_maintenance_record(
    db: AsyncSession,
    maintenance_data: MaintenanceRecordCreate,
) -> MaintenanceRecord:
    record = MaintenanceRecord(**maintenance_data.model_dump())

    db.add(record)
    await db.commit()
    await db.refresh(record)

    return record


async def get_maintenance_record_by_id(
    db: AsyncSession,
    record_id: int,
) -> MaintenanceRecord | None:
    result = await db.execute(
        select(MaintenanceRecord).where(
            MaintenanceRecord.id == record_id
        )
    )

    return result.scalar_one_or_none()


async def get_maintenance_records(
    db: AsyncSession,
) -> list[MaintenanceRecord]:
    result = await db.execute(
        select(MaintenanceRecord).order_by(
            MaintenanceRecord.created_at.desc()
        )
    )

    return list(result.scalars().all())


async def get_maintenance_records_by_machine(
    db: AsyncSession,
    machine_id: int,
) -> list[MaintenanceRecord]:
    result = await db.execute(
        select(MaintenanceRecord)
        .where(MaintenanceRecord.machine_id == machine_id)
        .order_by(MaintenanceRecord.created_at.desc())
    )

    return list(result.scalars().all())


async def update_maintenance_record(
    db: AsyncSession,
    record: MaintenanceRecord,
    maintenance_data: MaintenanceRecordUpdate,
) -> MaintenanceRecord:
    update_data = maintenance_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(record, field, value)

    await db.commit()
    await db.refresh(record)

    return record