"""add first_login to users

Revision ID: f92367f8b1a0
Revises: 87e54712f980
Create Date: 2025-10-31 15:06:17.269101

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f92367f8b1a0'
down_revision: Union[str, Sequence[str], None] = '87e54712f980'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("first_login", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    # optional: drop server_default post-creation (keeps DB clean)
    op.alter_column("users", "first_login", server_default=None)

def downgrade():
    op.drop_column("users", "first_login")