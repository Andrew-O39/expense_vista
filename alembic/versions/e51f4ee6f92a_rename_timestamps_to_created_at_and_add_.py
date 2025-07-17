"""Rename timestamps to created_at and add to user

Revision ID: e51f4ee6f92a
Revises: f0a72d0184d8
Create Date: 2025-07-17 01:45:32.422597

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e51f4ee6f92a'
down_revision: Union[str, Sequence[str], None] = 'f0a72d0184d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Expense: rename column
    op.alter_column('expenses', 'timestamp', new_column_name='created_at')

    # AlertLog: rename column
    op.alter_column('alert_logs', 'date_sent', new_column_name='created_at')

    # User: add created_at column
    op.add_column('users', sa.Column('created_at', sa.DateTime(), nullable=True))

    # Optional: backfill created_at for existing users
    op.execute("UPDATE users SET created_at = NOW() WHERE created_at IS NULL")

    # Make the column non-nullable
    op.alter_column('users', 'created_at', nullable=False)


def downgrade():
    op.alter_column('expenses', 'created_at', new_column_name='timestamp')
    op.alter_column('alert_logs', 'created_at', new_column_name='date_sent')
    op.drop_column('users', 'created_at')