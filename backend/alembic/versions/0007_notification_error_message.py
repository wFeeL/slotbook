"""add error_message to notifications

Revision ID: d4c1e8b9cf67
Revises: f3a1b2c4d5e6
Create Date: 2026-05-23 02:41:30.200006

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op



revision: str = 'd4c1e8b9cf67'
down_revision: str | None = 'f3a1b2c4d5e6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('notifications', sa.Column('error_message', sa.String(length=1000), nullable=True))


def downgrade() -> None:
    op.drop_column('notifications', 'error_message')
