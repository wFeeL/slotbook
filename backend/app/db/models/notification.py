from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.enums import NotificationStatus, NotificationType

notification_type_enum = sa.Enum(
    NotificationType,
    name="notification_type",
    values_callable=lambda obj: [e.value for e in obj],
    create_type=False,
)
notification_status_enum = sa.Enum(
    NotificationStatus,
    name="notification_status",
    values_callable=lambda obj: [e.value for e in obj],
    create_type=False,
)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    booking_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        notification_type_enum, nullable=False
    )
    notification_status: Mapped[NotificationStatus] = mapped_column(
        notification_status_enum, nullable=False, default=NotificationStatus.PENDING
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index(
            "ix_notifications_status_scheduled",
            "notification_status",
            "scheduled_at",
        ),
    )
