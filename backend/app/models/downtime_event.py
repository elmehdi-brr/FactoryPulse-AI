from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DowntimeEvent(Base):
    __tablename__ = "downtime_events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    production_run_id: Mapped[int] = mapped_column(
        ForeignKey(
            "production_runs.id",
            name="fk_downtime_events_production_run_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    machine_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "machines.id",
            name="fk_downtime_events_machine_id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    category: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    reason: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    production_run: Mapped["ProductionRun"] = relationship(
        back_populates="downtime_events"
    )

    machine: Mapped["Machine | None"] = relationship(
        back_populates="downtime_events"
    )