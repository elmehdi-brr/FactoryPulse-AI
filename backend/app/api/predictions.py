from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import require_roles
from app.core.rbac import ALL_ROLES, TECHNICAL_WRITE_ROLES
from app.db.session import get_db
from app.models.user import User
from app.schemas.prediction import PredictionCreate, PredictionResponse
from app.services.prediction_service import (
    create_prediction,
    get_prediction_by_id,
    get_prediction_by_source_and_model,
    get_predictions,
    get_predictions_by_sensor,
)
from app.services.sensor_service import get_sensor_by_id
from app.services.sensor_reading_service import get_sensor_reading_by_id


router = APIRouter(
    tags=["Predictions"],
)


@router.post(
    "/predictions",
    response_model=PredictionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_prediction_endpoint(
    prediction_data: PredictionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*TECHNICAL_WRITE_ROLES)),
) -> PredictionResponse:
    sensor = await get_sensor_by_id(
        db,
        prediction_data.sensor_id,
    )

    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found",
        )

    if prediction_data.source_reading_id is not None:
        source_reading = await get_sensor_reading_by_id(
            db,
            prediction_data.source_reading_id,
        )

        if source_reading is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source sensor reading not found",
            )

        if source_reading.sensor_id != prediction_data.sensor_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source reading does not belong to the selected sensor",
            )

        existing_prediction = await get_prediction_by_source_and_model(
            db,
            source_reading_id=prediction_data.source_reading_id,
            model_name=prediction_data.model_name,
            model_version=prediction_data.model_version,
        )

        if existing_prediction is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Prediction already exists for this source reading "
                    "and model version"
                ),
            )

    try:
        return await create_prediction(
            db,
            prediction_data,
        )
    except IntegrityError:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Prediction already exists for this source reading "
                "and model version"
            ),
        )


@router.get(
    "/predictions",
    response_model=list[PredictionResponse],
)
async def get_predictions_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> list[PredictionResponse]:
    return await get_predictions(db)


@router.get(
    "/predictions/{prediction_id}",
    response_model=PredictionResponse,
)
async def get_prediction_endpoint(
    prediction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> PredictionResponse:
    prediction = await get_prediction_by_id(db, prediction_id)

    if prediction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found",
        )

    return prediction


@router.get(
    "/sensors/{sensor_id}/predictions",
    response_model=list[PredictionResponse],
)
async def get_sensor_predictions_endpoint(
    sensor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> list[PredictionResponse]:
    sensor = await get_sensor_by_id(db, sensor_id)

    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found",
        )

    return await get_predictions_by_sensor(db, sensor_id)