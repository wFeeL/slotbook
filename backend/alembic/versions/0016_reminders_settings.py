"""reminder settings on business and user

Revision ID: 0016_reminders_settings
Revises: 0015_staff_user_unique
Create Date: 2026-05-24
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016_reminders_settings"
down_revision: str | Sequence[str] | None = "0015_staff_user_unique"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "businesses",
        sa.Column(
            "reminder_long_hours",
            sa.Integer(),
            nullable=False,
            server_default="24",
        ),
    )
    op.add_column(
        "businesses",
        sa.Column(
            "reminder_short_hours",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "reminders_enabled",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "reminders_enabled")
    op.drop_column("businesses", "reminder_short_hours")
    op.drop_column("businesses", "reminder_long_hours")
