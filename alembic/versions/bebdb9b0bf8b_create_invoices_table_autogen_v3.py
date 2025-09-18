"""create invoices table (autogen v3)

Revision ID: bebdb9b0bf8b
Revises: 0204af72d13a
Create Date: 2025-09-14 01:15:43.719254

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bebdb9b0bf8b'
down_revision: Union[str, Sequence[str], None] = '0204af72d13a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
