"""enforce production run non overlap

Revision ID: 9965bd5ba936
Revises: 58633c31421f
Create Date: 2026-08-27 01:37:11.293297
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "9965bd5ba936"
down_revision: Union[str, Sequence[str], None] = "58633c31421f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CONSTRAINT_NAME = "ex_production_runs_line_time_overlap"


def upgrade() -> None:
    """Prevent overlapping production runs on the same line."""

    op.execute(
        "CREATE EXTENSION IF NOT EXISTS btree_gist"
    )

    op.execute(
        f"""
        ALTER TABLE production_runs
        ADD CONSTRAINT {CONSTRAINT_NAME}
        EXCLUDE USING gist (
            production_line_id WITH =,
            tstzrange(
                started_at,
                COALESCE(
                    ended_at,
                    'infinity'::timestamptz
                ),
                '[)'
            ) WITH &&
        )
        """
    )


def downgrade() -> None:
    """Remove production run overlap protection."""

    op.execute(
        f"""
        ALTER TABLE production_runs
        DROP CONSTRAINT IF EXISTS {CONSTRAINT_NAME}
        """
    )