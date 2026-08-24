from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SensorAIConfigBase(BaseModel):
    is_enabled: bool = True

    engine_name: Literal[
        "statistical-zscore"
    ] = "statistical-zscore"

    anomaly_threshold: float = Field(
        default=3.0,
        gt=0,
    )

    min_history: int = Field(
        default=10,
        ge=2,
    )

    history_limit: int = Field(
        default=50,
        ge=2,
    )

    high_risk_threshold: float = Field(
        default=5.0,
        gt=0,
    )

    critical_risk_threshold: float = Field(
        default=8.0,
        gt=0,
    )

    @model_validator(mode="after")
    def validate_threshold_relationships(self) -> Self:
        if self.history_limit < self.min_history:
            raise ValueError(
                "history_limit must be greater than or equal "
                "to min_history"
            )

        if self.critical_risk_threshold <= self.high_risk_threshold:
            raise ValueError(
                "critical_risk_threshold must be greater than "
                "high_risk_threshold"
            )

        return self


class SensorAIConfigCreate(SensorAIConfigBase):
    pass


class SensorAIConfigUpdate(BaseModel):
    is_enabled: bool | None = None

    engine_name: Literal[
        "statistical-zscore"
    ] | None = None

    anomaly_threshold: float | None = Field(
        default=None,
        gt=0,
    )

    min_history: int | None = Field(
        default=None,
        ge=2,
    )

    history_limit: int | None = Field(
        default=None,
        ge=2,
    )

    high_risk_threshold: float | None = Field(
        default=None,
        gt=0,
    )

    critical_risk_threshold: float | None = Field(
        default=None,
        gt=0,
    )

    @model_validator(mode="after")
    def reject_explicit_nulls(self) -> Self:
        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(
                    f"{field_name} cannot be null"
                )

        return self


class SensorAIConfigResponse(SensorAIConfigBase):
    id: int
    sensor_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)