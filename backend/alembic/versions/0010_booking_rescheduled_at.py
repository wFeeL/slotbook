"""booking rescheduled_at

Revision ID: 0010_booking_rescheduled_at
Revises: 0009_booking_exclude_overlap
Create Date: 2026-05-23
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_booking_rescheduled_at"
down_revision: str | Sequence[str] | None = "0009_booking_exclude_overlap"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "bookings",
        sa.Column("rescheduled_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("bookings", "rescheduled_at")
