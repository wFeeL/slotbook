from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import NotificationStatus, NotificationType
from app.db.models.notification import Notification


class NotificationsRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, notification: Notification) -> None:
        self.session.add(notification)

    async def list_pending_for_booking(self, booking_id: int) -> list[Notification]:
        stmt = (
            select(Notification)
            .where(
                Notification.booking_id == booking_id,
                Notification.notification_status == NotificationStatus.PENDING,
            )
            .order_by(Notification.id)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def list_pending_due(self, now_utc: datetime, limit: int = 200) -> list[Notification]:
        """Pending notifications whose scheduled_at is in the past (i.e. ready to fire).

        Notifications with scheduled_at=NULL are NOT returned by this query — those
        are dispatched synchronously by the API process via NotificationService.
        """
        stmt = (
            select(Notification)
            .where(
                Notification.notification_status == NotificationStatus.PENDING,
                Notification.scheduled_at.is_not(None),
                Notification.scheduled_at <= now_utc,
            )
            .order_by(Notification.scheduled_at)
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def delete_pending_reminders_for_booking(self, booking_id: int) -> int:
        """Hard-delete still-pending REMINDER_* rows for a booking. Returns count deleted."""
        stmt = delete(Notification).where(
            Notification.booking_id == booking_id,
            Notification.notification_status == NotificationStatus.PENDING,
            Notification.notification_type.in_(
                (NotificationType.REMINDER_24H, NotificationType.REMINDER_2H)
            ),
        )
        result = await self.session.execute(stmt)
        return result.rowcount or 0
