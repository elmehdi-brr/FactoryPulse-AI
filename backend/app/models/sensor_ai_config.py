from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SensorAIConfig(Base):
    __tablename__ = "sensor_ai_configs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    sensor_id: Mapped[int] = mapped_column(
        ForeignKey(
            "sensors.id",
            ondelete="CASCADE",
        ),
        unique=True,
        nullable=False,
    )

    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    engine_name: Mapped[str] = mapped_column(
        String(100),
        default="statistical-zscore",
        nullable=False,
    )

    anomaly_threshold: Mapped[float] = mapped_column(
        Float,
        default=3.0,
        nullable=False,
    )

    min_history: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )

    history_limit: Mapped[int] = mapped_column(
        Integer,
        default=50,
        nullable=False,
    )

    high_risk_threshold: Mapped[float] = mapped_column(
        Float,
        default=5.0,
        nullable=False,
    )

    critical_risk_threshold: Mapped[float] = mapped_column(
        Float,
        default=8.0,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    sensor: Mapped["Sensor"] = relationship(
        back_populates="ai_config"
    )