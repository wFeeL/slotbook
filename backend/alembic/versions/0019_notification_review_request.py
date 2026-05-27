"""notification review request

Revision ID: 0019_notification_review_request
Revises: 0018_reviews_with_aggregates
Create Date: 2026-05-25
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0019_notification_review_request"
down_revision: str | Sequence[str] | None = "0018_reviews_with_aggregates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'review_request'"
    )
    # commit the enum value so it's visible in the subsequent index DDL
    op.execute("COMMIT")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_review_request_per_booking "
        "ON notifications (booking_id) "
        "WHERE notification_type = 'review_request'"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ux_review_request_per_booking")
