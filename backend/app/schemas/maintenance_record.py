from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


MaintenanceType = Literal[
    "preventive",
    "corrective",
]

MaintenanceStatus = Literal[
    "planned",
    "in_progress",
    "completed",
    "verified",
    "cancelled",
]


class MaintenanceRecordBase(BaseModel):
    machine_id: int
    alert_id: int | None = None
    performed_by_user_id: int | None = None
    maintenance_type: MaintenanceType
    description: str
    status: MaintenanceStatus = "planned"
    performed_at: datetime | None = None


class MaintenanceRecordCreate(MaintenanceRecordBase):
    pass


class MaintenanceRecordUpdate(BaseModel):
    alert_id: int | None = None
    performed_by_user_id: int | None = None
    maintenance_type: MaintenanceType | None = None
    description: str | None = None
    status: MaintenanceStatus | None = None
    performed_at: datetime | None = None


class MaintenanceRecordResponse(MaintenanceRecordBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)