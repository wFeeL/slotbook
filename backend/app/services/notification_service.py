from __future__ import annotations

from datetime import UTC, datetime

import structlog
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.texts import render
from app.core.config import get_settings
from app.db.enums import NotificationStatus
from app.db.models.notification import Notification
from app.db.repositories.bookings import BookingsRepo
from app.db.repositories.businesses import BusinessesRepo
from app.db.repositories.notifications import NotificationsRepo
from app.db.repositories.services import ServicesRepo
from app.db.repositories.staff import StaffRepo
from app.db.repositories.users import UsersRepo

log = structlog.get_logger()


class NotificationService:
    """Dispatches pending notifications via aiogram.Bot. Used by the API process."""

    def __init__(self, session: AsyncSession, bot: Bot) -> None:
        self.session = session
        self.bot = bot

    async def dispatch_pending_for_booking(self, booking_id: int) -> None:
        """Dispatch immediate (scheduled_at IS NULL) pending notifications for a booking."""
        notifications = await NotificationsRepo(self.session).list_pending_for_booking(booking_id)
        await self._dispatch_notifications(booking_id, notifications)

    async def dispatch_notifications(
        self, booking_id: int, notifications: list[Notification]
    ) -> None:
        """Dispatch the given pending notifications for a booking. Used by the worker."""
        await self._dispatch_notifications(booking_id, notifications)

    async def _dispatch_notifications(
        self, booking_id: int, notifications: list[Notification]
    ) -> None:
        if not notifications:
            return

        booking = await BookingsRepo(self.session).get(booking_id)
        if booking is None:
            log.warning("notification.booking_missing", booking_id=booking_id)
            return

        service = await ServicesRepo(self.session).get(booking.service_id)
        staff = await StaffRepo(self.session).get(booking.staff_id)
        business = await BusinessesRepo(self.session).get_singleton()
        if service is None or staff is None or business is None:
            log.warning(
                "notification.dependencies_missing",
                booking_id=booking_id,
                has_service=service is not None,
                has_staff=staff is not None,
                has_business=business is not None,
            )
            for n in notifications:
                n.notification_status = NotificationStatus.FAILED
                n.error_message = "Required entity missing (service/staff/business)"
            await self.session.commit()
            return

        settings = get_settings()
        client_user = await UsersRepo(self.session).get_by_id(booking.client_id)
        for n in notifications:
            recipient = await UsersRepo(self.session).get_by_id(n.user_id)
            if recipient is None:
                n.notification_status = NotificationStatus.FAILED
                n.error_message = "Recipient user not found"
                continue
            try:
                text, keyboard = render(
                    n,
                    booking=booking,
                    service=service,
                    staff=staff,
                    business=business,
                    mini_app_url=settings.MINI_APP_URL,
                    client=client_user,
                )
                await self.bot.send_message(
                    chat_id=recipient.telegram_id,
                    text=text,
                    reply_markup=keyboard,
                )
                n.notification_status = NotificationStatus.SENT
                n.sent_at = datetime.now(UTC)
            except TelegramAPIError as exc:
                from app.services.notification_retry import MAX_RETRIES, next_retry_at
                if n.retry_count + 1 >= MAX_RETRIES:
                    n.notification_status = NotificationStatus.FAILED
                    n.error_message = str(exc)[:1000]
                else:
                    n.retry_count += 1
                    n.next_retry_at = next_retry_at(n.retry_count - 1)
                    n.error_message = str(exc)[:1000]
                log.warning(
                    "notification.send_failed",
                    id=n.id,
                    type=n.notification_type.value,
                    retry_count=n.retry_count,
                    will_retry=n.notification_status == NotificationStatus.PENDING,
                    error=str(exc),
                )

        await self.session.commit()
