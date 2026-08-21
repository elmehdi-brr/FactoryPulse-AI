from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProductionLineBase(BaseModel):
    area_id: int
    name: str
    code: str
    description: str | None = None


class ProductionLineCreate(ProductionLineBase):
    pass


class ProductionLineUpdate(BaseModel):
    area_id: int | None = None
    name: str | None = None
    code: str | None = None
    description: str | None = None


class ProductionLineResponse(ProductionLineBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)