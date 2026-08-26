from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


ProductionRunStatus = Literal[
    "running",
    "completed",
    "cancelled",
]


class ProductionRunBase(BaseModel):
    production_line_id: int

    started_at: datetime
    ended_at: datetime | None = None

    status: ProductionRunStatus = "running"

    target_quantity: int | None = Field(
        default=None,
        gt=0,
    )

    total_quantity: int = Field(
        default=0,
        ge=0,
    )

    good_quantity: int = Field(
        default=0,
        ge=0,
    )

    reject_quantity: int = Field(
        default=0,
        ge=0,
    )

    ideal_cycle_time_seconds: float | None = Field(
        default=None,
        gt=0,
    )

    @model_validator(mode="after")
    def validate_production_run(
        self,
    ) -> "ProductionRunBase":
        if (
            self.ended_at is not None
            and self.ended_at < self.started_at
        ):
            raise ValueError(
                "ended_at cannot be earlier than started_at"
            )

        if (
            self.good_quantity
            + self.reject_quantity
            > self.total_quantity
        ):
            raise ValueError(
                "good_quantity and reject_quantity "
                "cannot exceed total_quantity"
            )

        if self.status == "running":
            if self.ended_at is not None:
                raise ValueError(
                    "running production runs cannot have ended_at"
                )

        if self.status in {
            "completed",
            "cancelled",
        }:
            if self.ended_at is None:
                raise ValueError(
                    "completed or cancelled production runs "
                    "require ended_at"
                )

        return self


class ProductionRunCreate(ProductionRunBase):
    pass


class ProductionRunUpdate(BaseModel):
    ended_at: datetime | None = None

    status: ProductionRunStatus | None = None

    target_quantity: int | None = Field(
        default=None,
        gt=0,
    )

    total_quantity: int | None = Field(
        default=None,
        ge=0,
    )

    good_quantity: int | None = Field(
        default=None,
        ge=0,
    )

    reject_quantity: int | None = Field(
        default=None,
        ge=0,
    )

    ideal_cycle_time_seconds: float | None = Field(
        default=None,
        gt=0,
    )


class ProductionRunResponse(ProductionRunBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )