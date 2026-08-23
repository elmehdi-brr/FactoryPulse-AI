from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.risk import AnomalyRiskEvaluator
from app.models.alert import Alert
from app.models.prediction import Prediction
from app.models.sensor_reading import SensorReading
from app.schemas.alert import AlertCreate
from app.services.alert_service import create_alert
from app.services.notification_automation_service import (
    create_notifications_for_alert,
)


DEFAULT_RISK_EVALUATOR = AnomalyRiskEvaluator(
    high_threshold=5.0,
    critical_threshold=8.0,
)


async def create_alert_for_prediction(
    db: AsyncSession,
    reading: SensorReading,
    prediction: Prediction,
    evaluator: AnomalyRiskEvaluator = DEFAULT_RISK_EVALUATOR,
) -> Alert | None:
    assessment = evaluator.assess(
        is_anomaly=prediction.is_anomaly,
        anomaly_score=prediction.anomaly_score,
    )

    if not assessment.should_alert:
        return None

    score_text = (
        "unavailable"
        if prediction.anomaly_score is None
        else f"{prediction.anomaly_score:.2f}"
    )

    alert_data = AlertCreate(
        sensor_id=prediction.sensor_id,
        prediction_id=prediction.id,
        severity=assessment.severity or "medium",
        title="AI anomaly detected",
        message=(
            f"Sensor reading {reading.id} with value "
            f"{reading.value} was classified as anomalous. "
            f"Expected value: {prediction.predicted_value:.2f}. "
            f"Anomaly score: {score_text}. "
            f"Model: {prediction.model_name} "
            f"{prediction.model_version or ''}."
        ),
        status="open",
    )

    alert = await create_alert(
        db,
        alert_data,
    )

    await create_notifications_for_alert(
        db,
        alert,
    )

    return alert