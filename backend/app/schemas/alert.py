from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertBase(BaseModel):
    sensor_id: int
    prediction_id: int | None = None
    severity: str
    title: str
    message: str
    status: str = "open"


class AlertCreate(AlertBase):
    pass


class AlertUpdate(BaseModel):
    severity: str | None = None
    title: str | None = None
    message: str | None = None
    status: str | None = None


class AlertResponse(AlertBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)