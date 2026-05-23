"""notification retries

Revision ID: 0008_notification_retries
Revises: d4c1e8b9cf67
Create Date: 2026-05-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008_notification_retries"
down_revision: str | Sequence[str] | None = "d4c1e8b9cf67"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "notifications",
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "notifications",
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_notifications_next_retry",
        "notifications",
        ["next_retry_at"],
        postgresql_where=sa.text("next_retry_at IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_next_retry", table_name="notifications")
    op.drop_column("notifications", "next_retry_at")
    op.drop_column("notifications", "retry_count")
