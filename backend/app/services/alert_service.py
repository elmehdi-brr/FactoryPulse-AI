from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.schemas.alert import AlertCreate, AlertUpdate


async def create_alert(
    db: AsyncSession,
    alert_data: AlertCreate,
) -> Alert:
    alert = Alert(**alert_data.model_dump())

    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    return alert


async def get_alert_by_id(
    db: AsyncSession,
    alert_id: int,
) -> Alert | None:
    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id
        )
    )

    return result.scalar_one_or_none()


async def get_alert_by_prediction_id(
    db: AsyncSession,
    prediction_id: int,
) -> Alert | None:
    result = await db.execute(
        select(Alert).where(
            Alert.prediction_id == prediction_id
        )
    )

    return result.scalar_one_or_none()


async def create_alert_idempotently(
    db: AsyncSession,
    alert_data: AlertCreate,
) -> Alert:
    prediction_id = alert_data.prediction_id

    if prediction_id is None:
        return await create_alert(
            db,
            alert_data,
        )

    existing_alert = await get_alert_by_prediction_id(
        db,
        prediction_id,
    )

    if existing_alert is not None:
        return existing_alert

    try:
        return await create_alert(
            db,
            alert_data,
        )
    except IntegrityError:
        await db.rollback()

        existing_alert = await get_alert_by_prediction_id(
            db,
            prediction_id,
        )

        if existing_alert is None:
            raise

        return existing_alert


async def get_alerts(
    db: AsyncSession,
) -> list[Alert]:
    result = await db.execute(
        select(Alert).order_by(
            Alert.created_at.desc()
        )
    )

    return list(result.scalars().all())


async def get_alerts_by_sensor(
    db: AsyncSession,
    sensor_id: int,
) -> list[Alert]:
    result = await db.execute(
        select(Alert)
        .where(
            Alert.sensor_id == sensor_id
        )
        .order_by(
            Alert.created_at.desc()
        )
    )

    return list(result.scalars().all())


async def update_alert(
    db: AsyncSession,
    alert: Alert,
    alert_data: AlertUpdate,
) -> Alert:
    update_data = alert_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(
            alert,
            field,
            value,
        )

    await db.commit()
    await db.refresh(alert)

    return alert