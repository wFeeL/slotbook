"""admin invites

Revision ID: 0012_admin_invites
Revises: 0011_notif_rescheduled_types
Create Date: 2026-05-23
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012_admin_invites"
down_revision: str | Sequence[str] | None = "0011_notif_rescheduled_types"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_invites",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "business_id",
            sa.BigInteger(),
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token", sa.String(64), nullable=False, unique=True),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column(
            "created_by_user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "consumed_by_user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_admin_invites_token", "admin_invites", ["token"], unique=True)
    op.create_index(
        "ix_admin_invites_business_active",
        "admin_invites",
        ["business_id", "consumed_at", "expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_admin_invites_business_active", table_name="admin_invites")
    op.drop_index("ix_admin_invites_token", table_name="admin_invites")
    op.drop_table("admin_invites")
