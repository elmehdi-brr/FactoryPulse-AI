from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SensorReadingBase(BaseModel):
    sensor_id: int
    value: float


class SensorReadingCreate(SensorReadingBase):
    pass


class SensorReadingResponse(SensorReadingBase):
    id: int
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)