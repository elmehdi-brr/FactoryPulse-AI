from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.machine import Machine
from app.models.sensor import Sensor
from app.models.sensor_reading import SensorReading
from app.schemas.machine_telemetry import (
    MachineSensorTelemetryResponse,
    MachineTelemetryReadingResponse,
    MachineTelemetryResponse,
)


class MachineTelemetryServiceError(ValueError):
    pass


async def calculate_machine_telemetry(
    db: AsyncSession,
    machine_id: int,
    limit_per_sensor: int = 12,
) -> MachineTelemetryResponse:
    if limit_per_sensor <= 0:
        raise MachineTelemetryServiceError(
            "limit_per_sensor must be greater than 0"
        )

    if limit_per_sensor > 100:
        raise MachineTelemetryServiceError(
            "limit_per_sensor cannot be greater than 100"
        )

    machine_result = await db.execute(
        select(Machine).where(
            Machine.id == machine_id
        )
    )

    machine = machine_result.scalar_one_or_none()

    if machine is None:
        raise MachineTelemetryServiceError(
            "Machine not found"
        )

    sensor_result = await db.execute(
        select(Sensor)
        .where(
            Sensor.machine_id == machine_id
        )
        .order_by(
            Sensor.id
        )
    )

    sensors = list(
        sensor_result.scalars().all()
    )

    if not sensors:
        return MachineTelemetryResponse(
            machine_id=machine_id,
            sensors=[],
        )

    ranked_readings = (
        select(
            SensorReading.id.label(
                "reading_id"
            ),
            SensorReading.sensor_id.label(
                "sensor_id"
            ),
            SensorReading.value.label(
                "value"
            ),
            SensorReading.recorded_at.label(
                "recorded_at"
            ),
            func.row_number()
            .over(
                partition_by=SensorReading.sensor_id,
                order_by=(
                    SensorReading.recorded_at.desc(),
                    SensorReading.id.desc(),
                ),
            )
            .label(
                "reading_rank"
            ),
        )
        .join(
            Sensor,
            SensorReading.sensor_id
            == Sensor.id,
        )
        .where(
            Sensor.machine_id == machine_id
        )
        .subquery()
    )

    reading_result = await db.execute(
        select(
            ranked_readings.c.reading_id,
            ranked_readings.c.sensor_id,
            ranked_readings.c.value,
            ranked_readings.c.recorded_at,
        )
        .where(
            ranked_readings.c.reading_rank
            <= limit_per_sensor
        )
        .order_by(
            ranked_readings.c.sensor_id,
            ranked_readings.c.recorded_at.desc(),
            ranked_readings.c.reading_id.desc(),
        )
    )

    readings_by_sensor: dict[
        int,
        list[MachineTelemetryReadingResponse],
    ] = defaultdict(list)

    for row in reading_result.all():
        readings_by_sensor[
            row.sensor_id
        ].append(
            MachineTelemetryReadingResponse(
                id=row.reading_id,
                value=float(row.value),
                recorded_at=row.recorded_at,
            )
        )

    telemetry_sensors = [
        MachineSensorTelemetryResponse(
            sensor_id=sensor.id,
            name=sensor.name,
            sensor_type=sensor.sensor_type,
            unit=sensor.unit,
            status=sensor.status,
            latest_reading=(
                readings_by_sensor[sensor.id][0]
                if readings_by_sensor[sensor.id]
                else None
            ),
            recent_readings=(
                readings_by_sensor[sensor.id]
            ),
        )
        for sensor in sensors
    ]

    return MachineTelemetryResponse(
        machine_id=machine_id,
        sensors=telemetry_sensors,
    )