from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"
    __table_args__ = (
        CheckConstraint(
            "maintenance_type IN ('preventive', 'corrective')",
            name="ck_maintenance_records_maintenance_type",
        ),
        CheckConstraint(
            (
                "status IN ("
                "'planned', "
                "'in_progress', "
                "'completed', "
                "'verified', "
                "'cancelled'"
                ")"
            ),
            name="ck_maintenance_records_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    machine_id: Mapped[int] = mapped_column(
        ForeignKey("machines.id"),
        nullable=False,
    )

    alert_id: Mapped[int | None] = mapped_column(
        ForeignKey("alerts.id"),
        nullable=True,
    )

    performed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    maintenance_type: Mapped[str] = mapped_column(String(50), nullable=False)

    description: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(
        String(30),
        default="planned",
        nullable=False,
    )

    performed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    machine: Mapped["Machine"] = relationship(back_populates="maintenance_records")
    alert: Mapped["Alert | None"] = relationship(back_populates="maintenance_records")
    performed_by: Mapped["User | None"] = relationship(back_populates="maintenance_records")