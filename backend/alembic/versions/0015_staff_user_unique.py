"""staff user partial unique index

Revision ID: 0015_staff_user_unique
Revises: 0014_notif_staff_types
Create Date: 2026-05-23
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0015_staff_user_unique"
down_revision: str | Sequence[str] | None = "0014_notif_staff_types"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_staff_user_active "
        "ON staff_members (user_id) "
        "WHERE user_id IS NOT NULL AND is_active = true"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ux_staff_user_active")
