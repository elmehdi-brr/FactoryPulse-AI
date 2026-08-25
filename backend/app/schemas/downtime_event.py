from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    model_validator,
)


DowntimeCategory = Literal[
    "planned",
    "unplanned",
]


class DowntimeEventBase(BaseModel):
    production_run_id: int

    machine_id: int | None = None

    category: DowntimeCategory

    reason: str

    started_at: datetime
    ended_at: datetime | None = None

    notes: str | None = None

    @model_validator(mode="after")
    def validate_downtime_event(
        self,
    ) -> "DowntimeEventBase":
        if (
            self.ended_at is not None
            and self.ended_at < self.started_at
        ):
            raise ValueError(
                "ended_at cannot be earlier than started_at"
            )

        return self


class DowntimeEventCreate(DowntimeEventBase):
    pass


class DowntimeEventUpdate(BaseModel):
    ended_at: datetime | None = None

    reason: str | None = None

    notes: str | None = None


class DowntimeEventResponse(DowntimeEventBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )