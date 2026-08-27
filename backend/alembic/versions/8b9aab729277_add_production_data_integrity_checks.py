"""add production data integrity checks

Revision ID: 8b9aab729277
Revises: 9965bd5ba936
Create Date: 2026-08-27 04:14:01.825290
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "8b9aab729277"
down_revision: Union[str, Sequence[str], None] = "9965bd5ba936"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add production and downtime data integrity checks."""

    op.create_check_constraint(
        "ck_production_runs_status",
        "production_runs",
        "status IN ('running', 'completed', 'cancelled')",
    )

    op.create_check_constraint(
        "ck_production_runs_status_end_consistency",
        "production_runs",
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
    )

    op.create_check_constraint(
        "ck_production_runs_time_order",
        "production_runs",
        """
        ended_at IS NULL
        OR ended_at >= started_at
        """,
    )

    op.create_check_constraint(
        "ck_production_runs_target_quantity_positive",
        "production_runs",
        """
        target_quantity IS NULL
        OR target_quantity > 0
        """,
    )

    op.create_check_constraint(
        "ck_production_runs_total_quantity_nonnegative",
        "production_runs",
        "total_quantity >= 0",
    )

    op.create_check_constraint(
        "ck_production_runs_good_quantity_nonnegative",
        "production_runs",
        "good_quantity >= 0",
    )

    op.create_check_constraint(
        "ck_production_runs_reject_quantity_nonnegative",
        "production_runs",
        "reject_quantity >= 0",
    )

    op.create_check_constraint(
        "ck_production_runs_quantity_consistency",
        "production_runs",
        """
        good_quantity + reject_quantity
        <= total_quantity
        """,
    )

    op.create_check_constraint(
        "ck_production_runs_ideal_cycle_positive",
        "production_runs",
        """
        ideal_cycle_time_seconds IS NULL
        OR ideal_cycle_time_seconds > 0
        """,
    )

    op.create_check_constraint(
        "ck_downtime_events_category",
        "downtime_events",
        "category IN ('planned', 'unplanned')",
    )

    op.create_check_constraint(
        "ck_downtime_events_time_order",
        "downtime_events",
        """
        ended_at IS NULL
        OR ended_at >= started_at
        """,
    )


def downgrade() -> None:
    """Remove production and downtime data integrity checks."""

    op.drop_constraint(
        "ck_downtime_events_time_order",
        "downtime_events",
        type_="check",
    )

    op.drop_constraint(
        "ck_downtime_events_category",
        "downtime_events",
        type_="check",
    )

    op.drop_constraint(
        "ck_production_runs_ideal_cycle_positive",
        "production_runs",
        type_="check",
    )

    op.drop_constraint(
        "ck_production_runs_quantity_consistency",
        "production_runs",
        type_="check",
    )

    op.drop_constraint(
        "ck_production_runs_reject_quantity_nonnegative",
        "production_runs",
        type_="check",
    )

    op.drop_constraint(
        "ck_production_runs_good_quantity_nonnegative",
        "production_runs",
        type_="check",
    )

    op.drop_constraint(
        "ck_production_runs_total_quantity_nonnegative",
        "production_runs",
        type_="check",
    )

    op.drop_constraint(
        "ck_production_runs_target_quantity_positive",
        "production_runs",
        type_="check",
    )

    op.drop_constraint(
        "ck_production_runs_time_order",
        "production_runs",
        type_="check",
    )

    op.drop_constraint(
        "ck_production_runs_status_end_consistency",
        "production_runs",
        type_="check",
    )

    op.drop_constraint(
        "ck_production_runs_status",
        "production_runs",
        type_="check",
    )