from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SensorBase(BaseModel):
    machine_id: int
    name: str
    sensor_type: str
    unit: str
    status: str = "active"


class SensorCreate(SensorBase):
    pass


class SensorUpdate(BaseModel):
    machine_id: int | None = None
    name: str | None = None
    sensor_type: str | None = None
    unit: str | None = None
    status: str | None = None


class SensorResponse(SensorBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)