from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AreaBase(BaseModel):
    site_id: int
    name: str
    code: str
    description: str | None = None


class AreaCreate(AreaBase):
    pass


class AreaUpdate(BaseModel):
    site_id: int | None = None
    name: str | None = None
    code: str | None = None
    description: str | None = None


class AreaResponse(AreaBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)