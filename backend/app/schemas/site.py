from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SiteBase(BaseModel):
    organization_id: int
    name: str
    code: str
    location: str | None = None
    description: str | None = None


class SiteCreate(SiteBase):
    pass


class SiteUpdate(BaseModel):
    organization_id: int | None = None
    name: str | None = None
    code: str | None = None
    location: str | None = None
    description: str | None = None


class SiteResponse(SiteBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)