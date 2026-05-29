from __future__ import annotations

import html
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram.types import InlineKeyboardMarkup

from app.bot.keyboards import (
    admin_new_booking_keyboard,
    client_booking_created_keyboard,
    staff_cabinet_keyboard,
)
from app.db.enums import NotificationType
from app.db.models.booking import Booking
from app.db.models.business import Business
from app.db.models.notification import Notification
from app.db.models.service import Service
from app.db.models.staff import StaffMember
from app.db.models.user import User


def _fmt_dt(dt: datetime, tz_name: str) -> str:
    """Render UTC datetime as HH:MM, dd MMMM (Russian short month) in business TZ."""
    months = [
        "января",
        "февраля",
        "марта",
        "апреля",
        "мая",
        "июня",
        "июля",
        "августа",
        "сентября",
        "октября",
        "ноября",
        "декабря",
    ]
    local = dt.astimezone(ZoneInfo(tz_name))
    return f"{local.strftime('%H:%M')}, {local.day} {months[local.month - 1]}"


def _esc(value: str | None) -> str:
    """Escape user-provided strings for HTML parse_mode."""
    return html.escape(value or "")


def render(
    notification: Notification,
    *,
    booking: Booking,
    service: Service,
    staff: StaffMember,
    business: Business,
    mini_app_url: str,
    client: User | None = None,
) -> tuple[str, InlineKeyboardMarkup | None]:
    """Render notification text + keyboard. Pure function."""
    when = _fmt_dt(booking.starts_at, business.timezone)
    service_title = _esc(service.title)
    staff_name = _esc(staff.name)
    comment = booking.client_comment

    # Per spec: if mini_app_url is not configured, skip the keyboard and send text only.
    # Telegram rejects WebApp buttons with empty/invalid URLs.
    def _kb(factory):
        return factory if mini_app_url else None

    if notification.notification_type == NotificationType.BOOKING_CREATED_CLIENT:
        text = (
            f"✅ <b>Запись подтверждена</b>\n\n"
            f"<b>Услуга:</b> {service_title}\n"
            f"<b>Специалист:</b> {staff_name}\n"
            f"<b>Время:</b> {when}\n"
            f"<b>Длительность:</b> {service.duration_minutes} мин"
        )
        return text, _kb(client_booking_created_keyboard(mini_app_url))

    if notification.notification_type == NotificationType.BOOKING_CREATED_ADMIN:
        text = (
            f"🔔 <b>Новая запись</b>\n\n"
            f"<b>Услуга:</b> {service_title}\n"
            f"<b>Специалист:</b> {staff_name}\n"
            f"<b>Время:</b> {when}\n"
            f"<b>Длительность:</b> {service.duration_minutes} мин"
        )
        if comment:
            text += f"\n<b>Комментарий клиента:</b> {_esc(comment)}"
        return text, _kb(admin_new_booking_keyboard(booking.id, mini_app_url))

    if notification.notification_type == NotificationType.BOOKING_CANCELLED_CLIENT:
        return (
            f"❌ <b>Запись отменена</b>\n\n<b>Услуга:</b> {service_title}\n<b>Время:</b> {when}"
        ), None

    if notification.notification_type == NotificationType.BOOKING_CANCELLED_ADMIN:
        return (
            f"❌ <b>Запись клиента отменена</b>\n\n"
            f"<b>Услуга:</b> {service_title}\n"
            f"<b>Специалист:</b> {staff_name}\n"
            f"<b>Время:</b> {when}"
        ), None

    if notification.notification_type == NotificationType.BOOKING_RESCHEDULED_CLIENT:
        text = (
            f"📅 <b>Запись перенесена</b>\n\n"
            f"<b>Услуга:</b> {service_title}\n"
            f"<b>Специалист:</b> {staff_name}\n"
            f"<b>Новое время:</b> {when}"
        )
        return text, _kb(client_booking_created_keyboard(mini_app_url))

    if notification.notification_type == NotificationType.BOOKING_RESCHEDULED_ADMIN:
        text = (
            f"📅 <b>Запись клиента перенесена</b>\n\n"
            f"<b>Услуга:</b> {service_title}\n"
            f"<b>Специалист:</b> {staff_name}\n"
            f"<b>Новое время:</b> {when}"
        )
        return text, _kb(admin_new_booking_keyboard(booking.id, mini_app_url))

    if notification.notification_type in (
        NotificationType.REMINDER_24H,
        NotificationType.REMINDER_2H,
    ):
        if notification.notification_type == NotificationType.REMINDER_2H:
            header = "⏰ <b>Напоминание</b> — через 2 часа у вас запись"  # noqa: RUF001
        else:
            header = "📅 <b>Напоминание</b> — через 24 часа у вас запись"  # noqa: RUF001
        text = (
            f"{header}\n\n"
            f"<b>Услуга:</b> {service_title}\n"
            f"<b>Специалист:</b> {staff_name}\n"
            f"<b>Время:</b> {when}"
        )
        return text, _kb(client_booking_created_keyboard(mini_app_url))

    client_name = _esc(client.first_name) if client and client.first_name else "Клиент"

    if notification.notification_type == NotificationType.BOOKING_CREATED_STAFF:
        text = (
            f"🗓 <b>Новая запись к вам</b>\n\n"
            f"<b>Услуга:</b> {service_title}\n"
            f"<b>Клиент:</b> {client_name}\n"
            f"<b>Время:</b> {when}\n"
            f"<b>Длительность:</b> {service.duration_minutes} мин"
        )
        if comment:
            text += f"\n<b>Комментарий:</b> {_esc(comment)}"
        return text, _kb(staff_cabinet_keyboard(mini_app_url))

    if notification.notification_type == NotificationType.BOOKING_CANCELLED_STAFF:
        text = (
            f"❌ <b>Запись отменена</b>\n\n"
            f"<b>Услуга:</b> {service_title}\n"
            f"<b>Клиент:</b> {client_name}\n"
            f"<b>Время:</b> {when}"
        )
        return text, _kb(staff_cabinet_keyboard(mini_app_url))

    if notification.notification_type == NotificationType.BOOKING_RESCHEDULED_STAFF:
        text = (
            f"📅 <b>Запись перенесена</b>\n\n"
            f"<b>Услуга:</b> {service_title}\n"
            f"<b>Клиент:</b> {client_name}\n"
            f"<b>Новое время:</b> {when}"
        )
        return text, _kb(staff_cabinet_keyboard(mini_app_url))

    if notification.notification_type == NotificationType.REVIEW_REQUEST:
        from app.bot.keyboards import review_request_keyboard
        text = (
            f"🌿 <b>Как прошла встреча?</b>\n\n"
            f"<b>Услуга:</b> {service_title}\n"
            f"<b>Мастер:</b> {staff_name}\n\n"
            f"Поставьте оценку — это поможет другим клиентам и нам стать лучше."
        )
        return text, _kb(review_request_keyboard(mini_app_url, booking.id))

    raise ValueError(f"Unknown notification type: {notification.notification_type}")
