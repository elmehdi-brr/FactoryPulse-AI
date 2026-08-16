from sqlalchemy import select
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
        select(Alert).where(Alert.id == alert_id)
    )

    return result.scalar_one_or_none()


async def get_alerts(
    db: AsyncSession,
) -> list[Alert]:
    result = await db.execute(
        select(Alert).order_by(Alert.created_at.desc())
    )

    return list(result.scalars().all())


async def get_alerts_by_sensor(
    db: AsyncSession,
    sensor_id: int,
) -> list[Alert]:
    result = await db.execute(
        select(Alert)
        .where(Alert.sensor_id == sensor_id)
        .order_by(Alert.created_at.desc())
    )

    return list(result.scalars().all())


async def update_alert(
    db: AsyncSession,
    alert: Alert,
    alert_data: AlertUpdate,
) -> Alert:
    update_data = alert_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(alert, field, value)

    await db.commit()
    await db.refresh(alert)

    return alert