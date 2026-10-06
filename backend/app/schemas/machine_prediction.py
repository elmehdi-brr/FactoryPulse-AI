from datetime import datetime

from pydantic import BaseModel


class MachinePredictionResponse(BaseModel):
    prediction_id: int

    sensor_id: int
    sensor_name: str
    sensor_type: str
    unit: str

    source_reading_id: int | None

    predicted_value: float
    anomaly_score: float | None
    is_anomaly: bool

    model_name: str
    model_version: str | None

    predicted_at: datetime


class MachinePredictionsResponse(BaseModel):
    machine_id: int
    predictions: list[
        MachinePredictionResponse
    ]