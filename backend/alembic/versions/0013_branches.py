"""branches

Revision ID: 0013_branches
Revises: 0012_admin_invites
Create Date: 2026-05-23
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013_branches"
down_revision: str | Sequence[str] | None = "0012_admin_invites"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create branches
    op.create_table(
        "branches",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "business_id",
            sa.BigInteger(),
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # 2. Seed a default branch per existing business
    op.execute(
        """
        INSERT INTO branches (business_id, name, timezone, is_active, sort_order, created_at, updated_at)
        SELECT id, name, timezone, TRUE, 0, NOW(), NOW() FROM businesses
        """
    )

    # 3. Add branch_id NULLABLE to services/staff/bookings
    op.add_column(
        "services",
        sa.Column(
            "branch_id",
            sa.BigInteger(),
            sa.ForeignKey("branches.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.add_column(
        "staff_members",
        sa.Column(
            "branch_id",
            sa.BigInteger(),
            sa.ForeignKey("branches.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.add_column(
        "bookings",
        sa.Column(
            "branch_id",
            sa.BigInteger(),
            sa.ForeignKey("branches.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )

    # 4. Backfill: every row gets the default branch of its business
    op.execute(
        """
        UPDATE services s SET branch_id = (
            SELECT id FROM branches WHERE business_id = s.business_id ORDER BY sort_order, id LIMIT 1
        )
        """
    )
    op.execute(
        """
        UPDATE staff_members st SET branch_id = (
            SELECT id FROM branches WHERE business_id = st.business_id ORDER BY sort_order, id LIMIT 1
        )
        """
    )
    op.execute(
        """
        UPDATE bookings b SET branch_id = (
            SELECT id FROM branches WHERE business_id = b.business_id ORDER BY sort_order, id LIMIT 1
        )
        """
    )

    # 5. NOT NULL
    op.alter_column("services", "branch_id", nullable=False)
    op.alter_column("staff_members", "branch_id", nullable=False)
    op.alter_column("bookings", "branch_id", nullable=False)

    op.create_index("ix_services_branch", "services", ["branch_id"])
    op.create_index("ix_staff_members_branch", "staff_members", ["branch_id"])
    op.create_index("ix_bookings_branch", "bookings", ["branch_id"])


def downgrade() -> None:
    op.drop_index("ix_bookings_branch", table_name="bookings")
    op.drop_index("ix_staff_members_branch", table_name="staff_members")
    op.drop_index("ix_services_branch", table_name="services")
    op.drop_column("bookings", "branch_id")
    op.drop_column("staff_members", "branch_id")
    op.drop_column("services", "branch_id")
    op.drop_table("branches")
