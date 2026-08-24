from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
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
        select(Prediction).where(
            Prediction.id == prediction_id
        )
    )

    return result.scalar_one_or_none()


async def get_prediction_by_source_and_model(
    db: AsyncSession,
    source_reading_id: int,
    model_name: str,
    model_version: str | None,
) -> Prediction | None:
    query = select(Prediction).where(
        Prediction.source_reading_id == source_reading_id,
        Prediction.model_name == model_name,
    )

    if model_version is None:
        query = query.where(
            Prediction.model_version.is_(None)
        )
    else:
        query = query.where(
            Prediction.model_version == model_version
        )

    result = await db.execute(query)

    return result.scalar_one_or_none()


async def create_prediction_idempotently(
    db: AsyncSession,
    prediction_data: PredictionCreate,
) -> Prediction:
    source_reading_id = prediction_data.source_reading_id

    if source_reading_id is None:
        return await create_prediction(
            db,
            prediction_data,
        )

    existing_prediction = (
        await get_prediction_by_source_and_model(
            db,
            source_reading_id,
            prediction_data.model_name,
            prediction_data.model_version,
        )
    )

    if existing_prediction is not None:
        return existing_prediction

    try:
        return await create_prediction(
            db,
            prediction_data,
        )
    except IntegrityError:
        await db.rollback()

        existing_prediction = (
            await get_prediction_by_source_and_model(
                db,
                source_reading_id,
                prediction_data.model_name,
                prediction_data.model_version,
            )
        )

        if existing_prediction is None:
            raise

        return existing_prediction


async def get_predictions(
    db: AsyncSession,
) -> list[Prediction]:
    result = await db.execute(
        select(Prediction).order_by(
            Prediction.predicted_at.desc()
        )
    )

    return list(result.scalars().all())


async def get_predictions_by_sensor(
    db: AsyncSession,
    sensor_id: int,
) -> list[Prediction]:
    result = await db.execute(
        select(Prediction)
        .where(
            Prediction.sensor_id == sensor_id
        )
        .order_by(
            Prediction.predicted_at.desc()
        )
    )

    return list(result.scalars().all())