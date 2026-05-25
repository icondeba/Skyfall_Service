"""add customer campaign fields

Revision ID: 001_customer_campaign
Revises:
Create Date: 2026-05-10 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "001_customer_campaign"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("customers", sa.Column("birthday", sa.Date(), nullable=True))
    op.add_column("customers", sa.Column("anniversary", sa.Date(), nullable=True))
    op.add_column("customers", sa.Column("special_event_date", sa.Date(), nullable=True))
    op.add_column("customers", sa.Column("special_event_name", sa.String(120), nullable=True))


def downgrade() -> None:
    op.drop_column("customers", "special_event_name")
    op.drop_column("customers", "special_event_date")
    op.drop_column("customers", "anniversary")
    op.drop_column("customers", "birthday")
