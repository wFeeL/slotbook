from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.notifications import NotificationsRepo

logger = structlog.get_logger(__name__)


class NotificationService:
    """Stub notification dispatcher — logs pending notifications without real sending."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def dispatch_pending_for_booking(self, booking_id: int) -> None:
        """Fetch pending notifications for a booking and log them (no real Bot API calls)."""
        notifications = await NotificationsRepo(self.session).list_pending_for_booking(booking_id)
        for notification in notifications:
            logger.info(
                "notification.pending",
                booking_id=booking_id,
                notification_id=notification.id,
                notification_type=notification.notification_type.value,
                user_id=notification.user_id,
            )
