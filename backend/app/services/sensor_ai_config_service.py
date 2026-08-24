from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.settings import AISettings, DEFAULT_AI_SETTINGS
from app.models.sensor_ai_config import SensorAIConfig
from app.schemas.sensor_ai_config import (
    SensorAIConfigCreate,
    SensorAIConfigUpdate,
)


class SensorAIConfigValidationError(ValueError):
    """Raised when the final AI configuration is invalid."""


async def get_sensor_ai_config_by_sensor_id(
    db: AsyncSession,
    sensor_id: int,
) -> SensorAIConfig | None:
    result = await db.execute(
        select(SensorAIConfig).where(
            SensorAIConfig.sensor_id == sensor_id
        )
    )

    return result.scalar_one_or_none()


async def create_sensor_ai_config(
    db: AsyncSession,
    sensor_id: int,
    config_data: SensorAIConfigCreate,
) -> SensorAIConfig:
    config = SensorAIConfig(
        sensor_id=sensor_id,
        **config_data.model_dump(),
    )

    db.add(config)

    await db.commit()
    await db.refresh(config)

    return config


async def update_sensor_ai_config(
    db: AsyncSession,
    config: SensorAIConfig,
    config_data: SensorAIConfigUpdate,
) -> SensorAIConfig:
    update_data = config_data.model_dump(
        exclude_unset=True,
    )

    current_data = {
        "is_enabled": config.is_enabled,
        "engine_name": config.engine_name,
        "anomaly_threshold": config.anomaly_threshold,
        "min_history": config.min_history,
        "history_limit": config.history_limit,
        "high_risk_threshold": config.high_risk_threshold,
        "critical_risk_threshold": config.critical_risk_threshold,
    }

    try:
        validated_config = SensorAIConfigCreate.model_validate(
            {
                **current_data,
                **update_data,
            }
        )
    except ValidationError as exc:
        first_error = exc.errors()[0]

        message = first_error.get(
            "msg",
            "Invalid Sensor AI configuration",
        )

        if message.startswith("Value error, "):
            message = message.removeprefix(
                "Value error, "
            )

        raise SensorAIConfigValidationError(
            message
        ) from exc

    for field, value in validated_config.model_dump().items():
        setattr(
            config,
            field,
            value,
        )

    await db.commit()
    await db.refresh(config)

    return config

async def resolve_sensor_ai_settings(
    db: AsyncSession,
    sensor_id: int,
) -> AISettings:
    config = await get_sensor_ai_config_by_sensor_id(
        db,
        sensor_id,
    )

    if config is None:
        return DEFAULT_AI_SETTINGS

    return AISettings(
        is_enabled=config.is_enabled,
        engine_name=config.engine_name,
        anomaly_threshold=config.anomaly_threshold,
        min_history=config.min_history,
        history_limit=config.history_limit,
        high_risk_threshold=config.high_risk_threshold,
        critical_risk_threshold=config.critical_risk_threshold,
    )