"""notification staff types

Revision ID: 0014_notif_staff_types
Revises: 0013_branches
Create Date: 2026-05-23
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0014_notif_staff_types"
down_revision: str | Sequence[str] | None = "0013_branches"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'booking_created_staff'")
    op.execute("ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'booking_cancelled_staff'")
    op.execute("ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'booking_rescheduled_staff'")


def downgrade() -> None:
    pass
