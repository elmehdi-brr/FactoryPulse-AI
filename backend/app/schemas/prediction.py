from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PredictionBase(BaseModel):
    sensor_id: int
    source_reading_id: int | None = None
    predicted_value: float
    anomaly_score: float | None = None
    is_anomaly: bool = False
    model_name: str
    model_version: str | None = None

class PredictionCreate(PredictionBase):
    pass


class PredictionResponse(PredictionBase):
    id: int
    predicted_at: datetime

    model_config = ConfigDict(from_attributes=True)