from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrganizationBase(BaseModel):
    name: str
    code: str
    description: str | None = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None


class OrganizationResponse(OrganizationBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)