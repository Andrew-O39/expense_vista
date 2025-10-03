"""add updated_at to password_reset_tokens

Revision ID: 16e26088b6cd
Revises: 7fe9c187f02c
Create Date: 2025-10-03 22:05:46.468749

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '16e26088b6cd'
down_revision: Union[str, Sequence[str], None] = '7fe9c187f02c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Option A (robust for existing rows): add nullable, backfill, then set NOT NULL
    op.add_column(
        "password_reset_tokens",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Backfill existing rows so we can safely make it NOT NULL
    op.execute("UPDATE password_reset_tokens SET updated_at = NOW() WHERE updated_at IS NULL")

    # Now enforce NOT NULL and set a server default for future inserts
    op.alter_column(
        "password_reset_tokens",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("NOW()"),
    )


def downgrade() -> None:
    op.drop_column("password_reset_tokens", "updated_at")