from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.enums import BookingSource, BookingStatus

booking_status_enum = sa.Enum(
    BookingStatus,
    name="booking_status",
    values_callable=lambda obj: [e.value for e in obj],
    create_type=False,
)
booking_source_enum = sa.Enum(
    BookingSource,
    name="booking_source",
    values_callable=lambda obj: [e.value for e in obj],
    create_type=False,
)


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    business_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    branch_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    client_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    staff_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("staff_members.id", ondelete="RESTRICT"), nullable=False
    )
    service_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("services.id", ondelete="RESTRICT"), nullable=False
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        booking_status_enum, nullable=False, default=BookingStatus.CONFIRMED
    )
    client_comment: Mapped[str | None] = mapped_column(Text)
    admin_comment: Mapped[str | None] = mapped_column(Text)
    source: Mapped[BookingSource] = mapped_column(
        booking_source_enum, nullable=False, default=BookingSource.MINI_APP
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rescheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="ck_bookings_end_after_start"),
        Index("ix_bookings_staff_starts", "staff_id", "starts_at"),
        Index("ix_bookings_client_starts", "client_id", "starts_at"),
        Index("ix_bookings_status", "status"),
    )
