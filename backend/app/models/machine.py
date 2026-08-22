from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Machine(Base):
    __tablename__ = "machines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    area_id: Mapped[int] = mapped_column(
        ForeignKey("areas.id"),
        nullable=False,
        index=True,
    )

    production_line_id: Mapped[int | None] = mapped_column(
        ForeignKey("production_lines.id"),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    location: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="active",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    area: Mapped["Area"] = relationship(
        back_populates="machines"
    )

    production_line: Mapped["ProductionLine | None"] = relationship(
        back_populates="machines"
    )

    sensors: Mapped[list["Sensor"]] = relationship(
        back_populates="machine"
    )

    maintenance_records: Mapped[list["MaintenanceRecord"]] = relationship(
        back_populates="machine"
    )