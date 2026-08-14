from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    sensor_id: Mapped[int] = mapped_column(
        ForeignKey("sensors.id"),
        nullable=False,
    )

    prediction_id: Mapped[int | None] = mapped_column(
        ForeignKey("predictions.id"),
        nullable=True,
    )

    severity: Mapped[str] = mapped_column(String(30), nullable=False)

    title: Mapped[str] = mapped_column(String(150), nullable=False)

    message: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(
        String(30),
        default="open",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    sensor: Mapped["Sensor"] = relationship(back_populates="alerts")
    prediction: Mapped["Prediction | None"] = relationship(back_populates="alerts")
    maintenance_records: Mapped[list["MaintenanceRecord"]] = relationship(back_populates="alert")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="alert")