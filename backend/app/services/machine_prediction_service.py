from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.machine import Machine
from app.models.prediction import Prediction
from app.models.sensor import Sensor
from app.schemas.machine_prediction import (
    MachinePredictionResponse,
    MachinePredictionsResponse,
)


class MachinePredictionServiceError(ValueError):
    pass


async def get_machine_predictions(
    db: AsyncSession,
    machine_id: int,
    limit: int = 20,
) -> MachinePredictionsResponse:
    if limit <= 0:
        raise MachinePredictionServiceError(
            "limit must be greater than 0"
        )

    if limit > 100:
        raise MachinePredictionServiceError(
            "limit cannot be greater than 100"
        )

    machine_result = await db.execute(
        select(Machine).where(
            Machine.id == machine_id
        )
    )

    machine = machine_result.scalar_one_or_none()

    if machine is None:
        raise MachinePredictionServiceError(
            "Machine not found"
        )

    result = await db.execute(
        select(
            Prediction,
            Sensor,
        )
        .join(
            Sensor,
            Prediction.sensor_id == Sensor.id,
        )
        .where(
            Sensor.machine_id == machine_id
        )
        .order_by(
            Prediction.predicted_at.desc(),
            Prediction.id.desc(),
        )
        .limit(limit)
    )

    predictions = [
        MachinePredictionResponse(
            prediction_id=prediction.id,
            sensor_id=sensor.id,
            sensor_name=sensor.name,
            sensor_type=sensor.sensor_type,
            unit=sensor.unit,
            source_reading_id=(
                prediction.source_reading_id
            ),
            predicted_value=(
                float(prediction.predicted_value)
            ),
            anomaly_score=(
                float(prediction.anomaly_score)
                if prediction.anomaly_score is not None
                else None
            ),
            is_anomaly=prediction.is_anomaly,
            model_name=prediction.model_name,
            model_version=prediction.model_version,
            predicted_at=prediction.predicted_at,
        )
        for prediction, sensor in result.all()
    ]

    return MachinePredictionsResponse(
        machine_id=machine.id,
        predictions=predictions,
    )