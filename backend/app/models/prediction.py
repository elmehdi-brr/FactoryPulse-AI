from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    sensor_id: Mapped[int] = mapped_column(
        ForeignKey("sensors.id"),
        nullable=False,
    )

    predicted_value: Mapped[float] = mapped_column(Float, nullable=False)

    anomaly_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    is_anomaly: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    model_name: Mapped[str] = mapped_column(String(100), nullable=False)

    model_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    predicted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    sensor: Mapped["Sensor"] = relationship(back_populates="predictions")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="prediction")