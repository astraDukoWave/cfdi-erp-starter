"""manual create invoices

Revision ID: a20fa3ff62ae
Revises: bebdb9b0bf8b
Create Date: 2025-09-14 01:30:30.372401

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a20fa3ff62ae'
down_revision: Union[str, Sequence[str], None] = 'bebdb9b0bf8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "invoices",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("idempotency_key", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("uuid", sa.String(), nullable=True),
        sa.Column("xml_url", sa.Text(), nullable=True),
        sa.Column("payload", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_invoices_idempotency_key"),
    )
    op.create_index("ix_invoices_status", "invoices", ["status"])
    op.create_index("ix_invoices_id", "invoices", ["id"])
    op.create_index("ix_invoices_idempotency_key", "invoices", ["idempotency_key"], unique=True)
    op.create_index("ix_invoices_uuid", "invoices", ["uuid"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_invoices_uuid", table_name="invoices")
    op.drop_index("ix_invoices_idempotency_key", table_name="invoices")
    op.drop_index("ix_invoices_id", table_name="invoices")
    op.drop_index("ix_invoices_status", table_name="invoices")
    op.drop_table("invoices")
