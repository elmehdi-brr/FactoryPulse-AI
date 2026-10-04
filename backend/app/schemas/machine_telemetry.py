from datetime import datetime

from pydantic import BaseModel


class MachineTelemetryReadingResponse(BaseModel):
    id: int
    value: float
    recorded_at: datetime


class MachineSensorTelemetryResponse(BaseModel):
    sensor_id: int
    name: str
    sensor_type: str
    unit: str
    status: str

    latest_reading: (
        MachineTelemetryReadingResponse | None
    )

    recent_readings: list[
        MachineTelemetryReadingResponse
    ]


class MachineTelemetryResponse(BaseModel):
    machine_id: int
    sensors: list[
        MachineSensorTelemetryResponse
    ]