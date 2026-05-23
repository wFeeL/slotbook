"""notification rescheduled types

Revision ID: 0011_notif_rescheduled_types
Revises: 0010_booking_rescheduled_at
Create Date: 2026-05-23
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0011_notif_rescheduled_types"
down_revision: str | Sequence[str] | None = "0010_booking_rescheduled_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE must run outside a transaction in older PG; the
    # default migration runner uses one transaction. Use op.execute with
    # autocommit-friendly statements via the connection.
    op.execute("ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'booking_rescheduled_client'")
    op.execute("ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'booking_rescheduled_admin'")


def downgrade() -> None:
    # PostgreSQL doesn't support removing enum values cleanly.
    # Leave the values in place; they're idempotent on re-upgrade.
    pass
