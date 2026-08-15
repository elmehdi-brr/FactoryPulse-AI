from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sensor import Sensor
from app.schemas.sensor import SensorCreate, SensorUpdate


async def create_sensor(
    db: AsyncSession,
    sensor_data: SensorCreate,
) -> Sensor:
    sensor = Sensor(**sensor_data.model_dump())

    db.add(sensor)
    await db.commit()
    await db.refresh(sensor)

    return sensor


async def get_sensor_by_id(
    db: AsyncSession,
    sensor_id: int,
) -> Sensor | None:
    result = await db.execute(
        select(Sensor).where(Sensor.id == sensor_id)
    )

    return result.scalar_one_or_none()


async def get_sensors(
    db: AsyncSession,
) -> list[Sensor]:
    result = await db.execute(
        select(Sensor).order_by(Sensor.id)
    )

    return list(result.scalars().all())


async def update_sensor(
    db: AsyncSession,
    sensor: Sensor,
    sensor_data: SensorUpdate,
) -> Sensor:
    update_data = sensor_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(sensor, field, value)

    await db.commit()
    await db.refresh(sensor)

    return sensor


async def delete_sensor(
    db: AsyncSession,
    sensor: Sensor,
) -> None:
    await db.delete(sensor)
    await db.commit()  