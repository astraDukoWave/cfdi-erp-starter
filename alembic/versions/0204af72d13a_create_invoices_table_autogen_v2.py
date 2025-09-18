"""create invoices table (autogen v2)

Revision ID: 0204af72d13a
Revises: eb7319350bee
Create Date: 2025-09-14 00:56:58.938051

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0204af72d13a'
down_revision: Union[str, Sequence[str], None] = 'eb7319350bee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
