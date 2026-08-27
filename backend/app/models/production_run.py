from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
    literal_column,
)
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProductionRun(Base):
    __tablename__ = "production_runs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    production_line_id: Mapped[int] = mapped_column(
        ForeignKey(
            "production_lines.id",
            name="fk_production_runs_production_line_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="running",
        server_default="running",
        nullable=False,
    )

    target_quantity: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    total_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    good_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    reject_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    ideal_cycle_time_seconds: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    production_line: Mapped["ProductionLine"] = relationship(
        back_populates="production_runs"
    )

    downtime_events: Mapped[list["DowntimeEvent"]] = relationship(
        back_populates="production_run",
        cascade="all, delete-orphan",
    )


ProductionRun.__table__.append_constraint(
    ExcludeConstraint(
        (
            ProductionRun.__table__.c.production_line_id,
            "=",
        ),
        (
            func.tstzrange(
                ProductionRun.__table__.c.started_at,
                func.coalesce(
                    ProductionRun.__table__.c.ended_at,
                    literal_column(
                        "'infinity'::timestamptz"
                    ),
                ),
                literal_column("'[)'"),
            ),
            "&&",
        ),
        name="ex_production_runs_line_time_overlap",
        using="gist",
    )
)