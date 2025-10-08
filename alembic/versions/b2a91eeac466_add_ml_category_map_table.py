"""add ml_category_map table

Revision ID: b2a91eeac466
Revises: 16e26088b6cd
Create Date: 2025-10-08 17:56:20.341933

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2a91eeac466'
down_revision: Union[str, Sequence[str], None] = '16e26088b6cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "ml_category_maps",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("pattern", sa.String(length=256), nullable=False),
        sa.Column("category", sa.String(length=128), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id", "pattern", name="uq_ml_map_user_pattern"),
    )
    op.create_index("ix_ml_map_user_pattern", "ml_category_maps", ["user_id", "pattern"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_ml_map_user_pattern", table_name="ml_category_maps")
    op.drop_table("ml_category_maps")
