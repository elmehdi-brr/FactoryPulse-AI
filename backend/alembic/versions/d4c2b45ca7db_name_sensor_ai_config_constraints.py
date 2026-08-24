"""name sensor ai config constraints

Revision ID: d4c2b45ca7db
Revises: e35fae4e7e30
Create Date: 2026-08-24 02:02:25.383155

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4c2b45ca7db'
down_revision: Union[str, Sequence[str], None] = 'e35fae4e7e30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Give Sensor AI configuration constraints explicit names."""

    op.execute(
        """
        ALTER TABLE sensor_ai_configs
        RENAME CONSTRAINT sensor_ai_configs_sensor_id_key
        TO uq_sensor_ai_configs_sensor_id
        """
    )

    op.execute(
        """
        ALTER TABLE sensor_ai_configs
        RENAME CONSTRAINT sensor_ai_configs_sensor_id_fkey
        TO fk_sensor_ai_configs_sensor_id
        """
    )


def downgrade() -> None:
    """Restore PostgreSQL-generated constraint names."""

    op.execute(
        """
        ALTER TABLE sensor_ai_configs
        RENAME CONSTRAINT uq_sensor_ai_configs_sensor_id
        TO sensor_ai_configs_sensor_id_key
        """
    )

    op.execute(
        """
        ALTER TABLE sensor_ai_configs
        RENAME CONSTRAINT fk_sensor_ai_configs_sensor_id
        TO sensor_ai_configs_sensor_id_fkey
        """
    )