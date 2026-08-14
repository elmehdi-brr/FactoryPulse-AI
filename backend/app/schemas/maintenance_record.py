from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MaintenanceRecordBase(BaseModel):
    machine_id: int
    alert_id: int | None = None
    performed_by_user_id: int | None = None
    maintenance_type: str
    description: str
    status: str = "planned"
    performed_at: datetime | None = None


class MaintenanceRecordCreate(MaintenanceRecordBase):
    pass


class MaintenanceRecordUpdate(BaseModel):
    alert_id: int | None = None
    performed_by_user_id: int | None = None
    maintenance_type: str | None = None
    description: str | None = None
    status: str | None = None
    performed_at: datetime | None = None


class MaintenanceRecordResponse(MaintenanceRecordBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)