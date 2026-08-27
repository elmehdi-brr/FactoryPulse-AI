from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
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

ProductionRun.__table__.append_constraint(
    CheckConstraint(
        "status IN ('running', 'completed', 'cancelled')",
        name="ck_production_runs_status",
    )
)

ProductionRun.__table__.append_constraint(
    CheckConstraint(
        """
        (
            status = 'running'
            AND ended_at IS NULL
        )
        OR
        (
            status IN ('completed', 'cancelled')
            AND ended_at IS NOT NULL
        )
        """,
        name="ck_production_runs_status_end_consistency",
    )
)

ProductionRun.__table__.append_constraint(
    CheckConstraint(
        """
        ended_at IS NULL
        OR ended_at >= started_at
        """,
        name="ck_production_runs_time_order",
    )
)

ProductionRun.__table__.append_constraint(
    CheckConstraint(
        """
        target_quantity IS NULL
        OR target_quantity > 0
        """,
        name="ck_production_runs_target_quantity_positive",
    )
)

ProductionRun.__table__.append_constraint(
    CheckConstraint(
        "total_quantity >= 0",
        name="ck_production_runs_total_quantity_nonnegative",
    )
)

ProductionRun.__table__.append_constraint(
    CheckConstraint(
        "good_quantity >= 0",
        name="ck_production_runs_good_quantity_nonnegative",
    )
)

ProductionRun.__table__.append_constraint(
    CheckConstraint(
        "reject_quantity >= 0",
        name="ck_production_runs_reject_quantity_nonnegative",
    )
)

ProductionRun.__table__.append_constraint(
    CheckConstraint(
        """
        good_quantity + reject_quantity
        <= total_quantity
        """,
        name="ck_production_runs_quantity_consistency",
    )
)

ProductionRun.__table__.append_constraint(
    CheckConstraint(
        """
        ideal_cycle_time_seconds IS NULL
        OR ideal_cycle_time_seconds > 0
        """,
        name="ck_production_runs_ideal_cycle_positive",
    )
)