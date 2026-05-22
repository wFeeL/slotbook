"""working_hours and schedule_exceptions

Revision ID: 69091c1537d3
Revises: da9533a52fcd
Create Date: 2026-05-23 00:15:55.978416

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "69091c1537d3"
down_revision: str | None = "da9533a52fcd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE schedule_exception_type"
        " AS ENUM ('day_off','extra_working_time','blocked_time')"
    )
    op.create_table(
        "schedule_exceptions",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("staff_id", sa.BigInteger(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column(
            "type",
            postgresql.ENUM(
                "day_off",
                "extra_working_time",
                "blocked_time",
                name="schedule_exception_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["staff_id"], ["staff_members.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_schedule_exceptions_staff_date",
        "schedule_exceptions",
        ["staff_id", "date"],
        unique=False,
    )
    op.create_table(
        "working_hours",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("staff_id", sa.BigInteger(), nullable=False),
        sa.Column("weekday", sa.SmallInteger(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.CheckConstraint("end_time > start_time", name="ck_working_hours_end_after_start"),
        sa.CheckConstraint("weekday >= 0 AND weekday <= 6", name="ck_working_hours_weekday"),
        sa.ForeignKeyConstraint(["staff_id"], ["staff_members.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_working_hours_staff_weekday",
        "working_hours",
        ["staff_id", "weekday"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_working_hours_staff_weekday", table_name="working_hours")
    op.drop_table("working_hours")
    op.drop_index("ix_schedule_exceptions_staff_date", table_name="schedule_exceptions")
    op.drop_table("schedule_exceptions")
    op.execute("DROP TYPE schedule_exception_type")
