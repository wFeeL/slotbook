"""notifications and audit_logs

Revision ID: f3a1b2c4d5e6
Revises: c2f269907d48
Create Date: 2026-05-23 01:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "f3a1b2c4d5e6"
down_revision: str | None = "c2f269907d48"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop the non-unique partial index from the bookings migration and replace with a
    # UNIQUE partial index so that concurrent INSERTs for the same staff+slot conflict.
    op.execute("DROP INDEX IF EXISTS bookings_active_by_staff")
    op.execute(
        "CREATE UNIQUE INDEX bookings_active_by_staff ON bookings (staff_id, starts_at) "
        "WHERE status IN ('pending', 'confirmed')"
    )

    # Create notification enum types explicitly (ORM uses create_type=False)
    op.execute(
        "CREATE TYPE notification_type AS ENUM ("
        "'booking_created_client','booking_created_admin',"
        "'reminder_24h','reminder_2h',"
        "'booking_cancelled_client','booking_cancelled_admin')"
    )
    op.execute("CREATE TYPE notification_status AS ENUM ('pending','sent','failed')")

    op.create_table(
        "notifications",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("booking_id", sa.BigInteger(), nullable=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "notification_type",
            postgresql.ENUM(
                "booking_created_client",
                "booking_created_admin",
                "reminder_24h",
                "reminder_2h",
                "booking_cancelled_client",
                "booking_cancelled_admin",
                name="notification_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "notification_status",
            postgresql.ENUM(
                "pending",
                "sent",
                "failed",
                name="notification_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notifications_status_scheduled",
        "notifications",
        ["notification_status", "scheduled_at"],
        unique=False,
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("actor_user_id", sa.BigInteger(), nullable=True),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_audit_entity",
        "audit_logs",
        ["entity_type", "entity_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_audit_entity", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_notifications_status_scheduled", table_name="notifications")
    op.drop_table("notifications")
    op.execute("DROP TYPE IF EXISTS notification_status")
    op.execute("DROP TYPE IF EXISTS notification_type")
    # Revert unique index back to non-unique
    op.execute("DROP INDEX IF EXISTS bookings_active_by_staff")
    op.execute(
        "CREATE INDEX bookings_active_by_staff ON bookings (staff_id, starts_at) "
        "WHERE status IN ('pending', 'confirmed')"
    )
