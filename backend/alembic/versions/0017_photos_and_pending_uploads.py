"""photos and pending uploads

Revision ID: 0017_photos_and_pending_uploads
Revises: 0016_reminders_settings
Create Date: 2026-05-25
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0017_photos_and_pending_uploads"
down_revision: str | Sequence[str] | None = "0016_reminders_settings"
branch_labels = None
depends_on = None

photo_owner_type = postgresql.ENUM(
    "service", "staff", name="photo_owner_type", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    photo_owner_type.create(bind, checkfirst=True)

    op.create_table(
        "photos",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("owner_type", photo_owner_type, nullable=False),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.Column("telegram_file_id", sa.String(255), nullable=False),
        sa.Column("telegram_file_unique_id", sa.String(64), nullable=False),
        sa.Column("mime_type", sa.String(64), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_photos_owner", "photos", ["owner_type", "owner_id", "sort_order"]
    )
    op.create_unique_constraint(
        "ux_photos_owner_unique_id",
        "photos",
        ["owner_type", "owner_id", "telegram_file_unique_id"],
    )

    op.create_table(
        "pending_photo_uploads",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "admin_user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("owner_type", photo_owner_type, nullable=False),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("pending_photo_uploads")
    op.drop_index("ix_photos_owner", table_name="photos")
    op.drop_table("photos")
    bind = op.get_bind()
    photo_owner_type.drop(bind, checkfirst=True)
