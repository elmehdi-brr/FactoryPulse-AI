from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MachineBase(BaseModel):
    name: str
    code: str
    location: str | None = None
    status: str = "active"


class MachineCreate(MachineBase):
    pass


class MachineUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    location: str | None = None
    status: str | None = None


class MachineResponse(MachineBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)