"""booking exclude overlap

Revision ID: 0009_booking_exclude_overlap
Revises: 0008_notification_retries
Create Date: 2026-05-23
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0009_booking_exclude_overlap"
down_revision: str | Sequence[str] | None = "0008_notification_retries"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute(
        """
        ALTER TABLE bookings
        ADD CONSTRAINT bookings_no_overlap
        EXCLUDE USING gist (
            staff_id WITH =,
            tstzrange(starts_at, ends_at, '[)') WITH &&
        ) WHERE (status IN ('pending', 'confirmed'))
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE bookings DROP CONSTRAINT IF EXISTS bookings_no_overlap")
    # Do NOT drop btree_gist -- other tables may use it
