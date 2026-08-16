from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import Prediction
from app.schemas.prediction import PredictionCreate


async def create_prediction(
    db: AsyncSession,
    prediction_data: PredictionCreate,
) -> Prediction:
    prediction = Prediction(**prediction_data.model_dump())

    db.add(prediction)
    await db.commit()
    await db.refresh(prediction)

    return prediction


async def get_prediction_by_id(
    db: AsyncSession,
    prediction_id: int,
) -> Prediction | None:
    result = await db.execute(
        select(Prediction).where(Prediction.id == prediction_id)
    )

    return result.scalar_one_or_none()


async def get_predictions(
    db: AsyncSession,
) -> list[Prediction]:
    result = await db.execute(
        select(Prediction).order_by(Prediction.predicted_at.desc())
    )

    return list(result.scalars().all())


async def get_predictions_by_sensor(
    db: AsyncSession,
    sensor_id: int,
) -> list[Prediction]:
    result = await db.execute(
        select(Prediction)
        .where(Prediction.sensor_id == sensor_id)
        .order_by(Prediction.predicted_at.desc())
    )

    return list(result.scalars().all())