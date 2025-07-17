"""Changed limit column to limit_amount

Revision ID: 0e3d6585697f
Revises: fe1e32665f45
Create Date: 2025-07-10 20:09:37.543999

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0e3d6585697f'
down_revision: Union[str, Sequence[str], None] = 'fe1e32665f45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('budgets', 'limit', new_column_name='limit_amount')


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('budgets', 'limit_amount', new_column_name='limit')
