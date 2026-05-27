from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import (
    BigInteger,
    DateTime,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.enums import PhotoOwnerType

photo_owner_type_enum = sa.Enum(
    PhotoOwnerType,
    name="photo_owner_type",
    create_type=False,
    native_enum=True,
    values_callable=lambda obj: [e.value for e in obj],
)


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    owner_type: Mapped[PhotoOwnerType] = mapped_column(photo_owner_type_enum, nullable=False)
    owner_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    telegram_file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    telegram_file_unique_id: Mapped[str] = mapped_column(String(64), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(64))
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_photos_owner", "owner_type", "owner_id", "sort_order"),
        UniqueConstraint(
            "owner_type",
            "owner_id",
            "telegram_file_unique_id",
            name="ux_photos_owner_unique_id",
        ),
    )
