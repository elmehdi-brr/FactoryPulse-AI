from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIProcessingState(Base):
    __tablename__ = "ai_processing_states"

    __table_args__ = (
        Index(
            "ux_ai_processing_states_reading_model_version",
            "source_reading_id",
            "model_name",
            "model_version",
            unique=True,
            postgresql_nulls_not_distinct=True,
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    source_reading_id: Mapped[int] = mapped_column(
        ForeignKey(
            "sensor_readings.id",
            name="fk_ai_processing_states_source_reading_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    model_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="processing",
        nullable=False,
    )

    attempt_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    first_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    last_attempt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source_reading: Mapped["SensorReading"] = relationship(
        back_populates="ai_processing_states"
    )