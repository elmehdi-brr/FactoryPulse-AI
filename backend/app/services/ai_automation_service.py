from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import InferenceEngine
from app.ai.processing import AIProcessingStatus
from app.ai.settings import (
    build_inference_engine,
    build_risk_evaluator,
)
from app.models.prediction import Prediction
from app.models.sensor_reading import SensorReading
from app.schemas.prediction import PredictionCreate
from app.services.ai_processing_state_service import (
    complete_ai_processing_attempt,
    start_ai_processing_attempt,
)
from app.services.alert_automation_service import (
    create_alert_for_prediction,
)
from app.services.prediction_service import (
    create_prediction_idempotently,
)
from app.services.sensor_ai_config_service import (
    resolve_sensor_ai_settings,
)
from app.services.sensor_reading_service import (
    get_recent_readings_before,
)


async def process_sensor_reading(
    db: AsyncSession,
    reading: SensorReading,
    engine: InferenceEngine | None = None,
    history_limit: int | None = None,
) -> Prediction | None:
    settings = await resolve_sensor_ai_settings(
        db,
        reading.sensor_id,
    )

    effective_engine = (
        engine
        if engine is not None
        else build_inference_engine(settings)
    )

    processing_state = await start_ai_processing_attempt(
        db,
        source_reading_id=reading.id,
        model_name=effective_engine.model_name,
        model_version=effective_engine.model_version,
    )

    processing_state_id = processing_state.id

    if not settings.is_enabled:
        await complete_ai_processing_attempt(
            db,
            processing_state_id,
            AIProcessingStatus.SKIPPED,
        )

        return None

    try:
        effective_history_limit = (
            history_limit
            if history_limit is not None
            else settings.history_limit
        )

        recent_readings = await get_recent_readings_before(
            db,
            reading,
            limit=effective_history_limit,
        )

        history = [
            historical_reading.value
            for historical_reading in reversed(
                recent_readings
            )
        ]

        inference_result = effective_engine.infer(
            current_value=reading.value,
            history=history,
        )

        prediction_data = PredictionCreate(
            sensor_id=reading.sensor_id,
            source_reading_id=reading.id,
            predicted_value=(
                inference_result.predicted_value
            ),
            anomaly_score=(
                inference_result.anomaly_score
            ),
            is_anomaly=(
                inference_result.is_anomaly
            ),
            model_name=(
                inference_result.model_name
            ),
            model_version=(
                inference_result.model_version
            ),
        )

        prediction = await create_prediction_idempotently(
            db,
            prediction_data,
        )

        risk_evaluator = build_risk_evaluator(
            settings
        )

        await create_alert_for_prediction(
            db,
            reading,
            prediction,
            evaluator=risk_evaluator,
        )

        await complete_ai_processing_attempt(
            db,
            processing_state_id,
            AIProcessingStatus.SUCCEEDED,
        )

        return prediction

    except Exception as exc:
        # A failed SQLAlchemy operation may leave the current
        # transaction unusable until rollback.
        await db.rollback()

        await complete_ai_processing_attempt(
            db,
            processing_state_id,
            AIProcessingStatus.FAILED,
            last_error=str(exc),
        )

        raise