"""add email verification

Revision ID: 87e54712f980
Revises: b2a91eeac466
Create Date: 2025-10-28 00:30:13.781236

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '87e54712f980'
down_revision: Union[str, Sequence[str], None] = 'b2a91eeac466'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("users", sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("users", sa.Column("verification_token_hash", sa.String(length=128), nullable=True))
    op.add_column("users", sa.Column("verification_token_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_users_verification_token_hash", "users", ["verification_token_hash"], unique=False)
    # drop server_default if you like
    op.alter_column("users", "is_verified", server_default=None)

def downgrade():
    op.drop_index("ix_users_verification_token_hash", table_name="users")
    op.drop_column("users", "verification_token_expires_at")
    op.drop_column("users", "verification_token_hash")
    op.drop_column("users", "is_verified")