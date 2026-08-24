from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (
        Index(
            "ux_predictions_source_model_version",
            "source_reading_id",
            "model_name",
            "model_version",
            unique=True,
            postgresql_where=text(
                "source_reading_id IS NOT NULL"
            ),
            postgresql_nulls_not_distinct=True,
        ),
    )
    

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    sensor_id: Mapped[int] = mapped_column(
        ForeignKey("sensors.id"),
        nullable=False,
    )
    source_reading_id: Mapped[int | None] = mapped_column(
        ForeignKey("sensor_readings.id"),
        nullable=True,
        index=True,
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
    source_reading: Mapped["SensorReading | None"] = relationship(back_populates="predictions")