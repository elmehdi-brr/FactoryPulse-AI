from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.ai.processing import AIProcessingStatus


class AIProcessingStateResponse(BaseModel):
    id: int

    source_reading_id: int

    model_name: str
    model_version: str | None

    status: AIProcessingStatus

    attempt_count: int

    first_started_at: datetime
    last_attempt_at: datetime
    completed_at: datetime | None

    last_error: str | None

    model_config = ConfigDict(from_attributes=True)