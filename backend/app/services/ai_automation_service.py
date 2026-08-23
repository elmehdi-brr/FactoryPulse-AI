from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import InferenceEngine
from app.ai.baseline import StatisticalZScoreEngine
from app.models.prediction import Prediction
from app.models.sensor_reading import SensorReading
from app.schemas.prediction import PredictionCreate
from app.services.prediction_service import create_prediction
from app.services.sensor_reading_service import get_recent_readings_before


DEFAULT_INFERENCE_ENGINE = StatisticalZScoreEngine(
    threshold=3.0,
    min_history=10,
)


async def process_sensor_reading(
    db: AsyncSession,
    reading: SensorReading,
    engine: InferenceEngine = DEFAULT_INFERENCE_ENGINE,
    history_limit: int = 50,
) -> Prediction:
    recent_readings = await get_recent_readings_before(
        db,
        reading,
        limit=history_limit,
    )

    history = [
        historical_reading.value
        for historical_reading in reversed(recent_readings)
    ]

    inference_result = engine.infer(
        current_value=reading.value,
        history=history,
    )

    prediction_data = PredictionCreate(
        sensor_id=reading.sensor_id,
        source_reading_id=reading.id,
        predicted_value=inference_result.predicted_value,
        anomaly_score=inference_result.anomaly_score,
        is_anomaly=inference_result.is_anomaly,
        model_name=inference_result.model_name,
        model_version=inference_result.model_version,
    )

    return await create_prediction(
        db,
        prediction_data,
    )