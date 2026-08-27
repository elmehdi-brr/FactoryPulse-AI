"""enforce maintenance record vocabulary

Revision ID: 08e0e906b398
Revises: 8b9aab729277
Create Date: 2026-08-27 06:29:33.278427
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "08e0e906b398"
down_revision: Union[str, Sequence[str], None] = "8b9aab729277"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enforce valid maintenance types and statuses."""

    op.create_check_constraint(
        "ck_maintenance_records_maintenance_type",
        "maintenance_records",
        "maintenance_type IN ('preventive', 'corrective')",
    )

    op.create_check_constraint(
        "ck_maintenance_records_status",
        "maintenance_records",
        (
            "status IN ("
            "'planned', "
            "'in_progress', "
            "'completed', "
            "'verified', "
            "'cancelled'"
            ")"
        ),
    )


def downgrade() -> None:
    """Remove maintenance vocabulary constraints."""

    op.drop_constraint(
        "ck_maintenance_records_status",
        "maintenance_records",
        type_="check",
    )

    op.drop_constraint(
        "ck_maintenance_records_maintenance_type",
        "maintenance_records",
        type_="check",
    )