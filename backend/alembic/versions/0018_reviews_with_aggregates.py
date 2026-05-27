"""reviews with aggregates on services and staff

Revision ID: 0018_reviews_with_aggregates
Revises: 0017_photos_and_pending_uploads
Create Date: 2026-05-25
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0018_reviews_with_aggregates"
down_revision: str | Sequence[str] | None = "0017_photos_and_pending_uploads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reviews",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "booking_id",
            sa.BigInteger(),
            sa.ForeignKey("bookings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "client_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column(
            "service_id", sa.BigInteger(), sa.ForeignKey("services.id"), nullable=False
        ),
        sa.Column(
            "staff_id",
            sa.BigInteger(),
            sa.ForeignKey("staff_members.id"),
            nullable=False,
        ),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("text", sa.String(2000), nullable=True),
        sa.Column(
            "is_hidden", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("admin_reply", sa.String(2000), nullable=True),
        sa.Column(
            "admin_reply_user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("admin_reply_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("booking_id", name="ux_reviews_booking"),
        sa.CheckConstraint(
            "rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"
        ),
    )
    op.create_index(
        "ix_reviews_service_public",
        "reviews",
        ["service_id", "is_hidden", "created_at"],
    )
    op.create_index(
        "ix_reviews_staff_public",
        "reviews",
        ["staff_id", "is_hidden", "created_at"],
    )

    op.add_column(
        "services", sa.Column("avg_rating", sa.Numeric(2, 1), nullable=True)
    )
    op.add_column(
        "services",
        sa.Column("review_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "staff_members", sa.Column("avg_rating", sa.Numeric(2, 1), nullable=True)
    )
    op.add_column(
        "staff_members",
        sa.Column("review_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("staff_members", "review_count")
    op.drop_column("staff_members", "avg_rating")
    op.drop_column("services", "review_count")
    op.drop_column("services", "avg_rating")
    op.drop_index("ix_reviews_staff_public", table_name="reviews")
    op.drop_index("ix_reviews_service_public", table_name="reviews")
    op.drop_table("reviews")
