"""add staff tracking to orders and invoices

Revision ID: 002_staff_tracking
Revises: 001_customer_campaign
Create Date: 2026-05-10 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "002_staff_tracking"
down_revision = "001_customer_campaign"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite does not support adding FK constraints via ALTER TABLE.
    # Columns are added as plain UUIDs; the FK relationship is enforced at the ORM level.
    op.add_column("orders", sa.Column("placed_by_staff_id", sa.String(36), nullable=True))
    op.add_column("invoices", sa.Column("billed_by_staff_id", sa.String(36), nullable=True))


def downgrade() -> None:
    op.drop_column("invoices", "billed_by_staff_id")
    op.drop_column("orders", "placed_by_staff_id")
