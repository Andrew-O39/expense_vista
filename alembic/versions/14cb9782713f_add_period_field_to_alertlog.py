"""Add period field to AlertLog

Revision ID: 14cb9782713f
Revises: ad17eda74e28
Create Date: 2025-07-17 04:31:48.589157

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '14cb9782713f'
down_revision: Union[str, Sequence[str], None] = 'ad17eda74e28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Step 1: Add the column as nullable
    op.add_column('alert_logs', sa.Column('period', sa.String(), nullable=True))

    # Step 2: Backfill existing rows with a default value ('monthly')
    op.execute("UPDATE alert_logs SET period = 'monthly' WHERE period IS NULL")

    # Step 3: Alter column to be non-nullable
    op.alter_column('alert_logs', 'period', nullable=False)


def downgrade():
    # Remove the column on downgrade
    op.drop_column('alert_logs', 'period')