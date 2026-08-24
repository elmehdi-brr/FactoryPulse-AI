from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sensor_reading import SensorReading
from app.schemas.sensor_reading import SensorReadingCreate


async def create_sensor_reading(
    db: AsyncSession,
    reading_data: SensorReadingCreate,
) -> SensorReading:
    reading = SensorReading(**reading_data.model_dump())

    db.add(reading)
    await db.commit()
    await db.refresh(reading)

    return reading


async def get_sensor_reading_by_id(
    db: AsyncSession,
    reading_id: int,
) -> SensorReading | None:
    result = await db.execute(
        select(SensorReading).where(SensorReading.id == reading_id)
    )

    return result.scalar_one_or_none()


async def get_sensor_readings(
    db: AsyncSession,
) -> list[SensorReading]:
    result = await db.execute(
        select(SensorReading).order_by(SensorReading.recorded_at.desc())
    )

    return list(result.scalars().all())


async def get_readings_by_sensor(
    db: AsyncSession,
    sensor_id: int,
) -> list[SensorReading]:
    result = await db.execute(
        select(SensorReading)
        .where(SensorReading.sensor_id == sensor_id)
        .order_by(SensorReading.recorded_at.desc())
    )

    return list(result.scalars().all())

async def get_recent_readings_before(
    db: AsyncSession,
    reading: SensorReading,
    limit: int = 50,
) -> list[SensorReading]:
    result = await db.execute(
        select(SensorReading)
        .where(
            SensorReading.sensor_id == reading.sensor_id,
            or_(
                SensorReading.recorded_at < reading.recorded_at,
                and_(
                    SensorReading.recorded_at == reading.recorded_at,
                    SensorReading.id < reading.id,
                ),
            ),
        )
        .order_by(
            SensorReading.recorded_at.desc(),
            SensorReading.id.desc(),
        )
        .limit(limit)
    )

    return list(result.scalars().all())