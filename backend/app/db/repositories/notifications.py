from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import NotificationStatus
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
