from __future__ import annotations

import structlog
from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import (
    CancellationTooLate,
    CannotCancelInCurrentStatus,
    Forbidden,
    NotFound,
)
from app.db.enums import UserRole
from app.db.repositories.businesses import BusinessesRepo
from app.db.repositories.users import UsersRepo
from app.services.booking_service import BookingService
from app.services.notification_service import NotificationService

log = structlog.get_logger()

router = Router(name="admin_callbacks")


@router.callback_query(F.data.startswith("cancel_booking:"))
async def handle_cancel_booking(
    callback: CallbackQuery, session: AsyncSession, bot: Bot
) -> None:
    if callback.data is None or callback.from_user is None:
        await callback.answer("Некорректный запрос", show_alert=True)
        return

    try:
        booking_id = int(callback.data.split(":", 1)[1])
    except (IndexError, ValueError):
        await callback.answer("Некорректный booking_id", show_alert=True)
        return

    # AUTH CHECK: must happen BEFORE any BookingService call
    actor = await UsersRepo(session).get_by_telegram_id(callback.from_user.id)
    if actor is None or actor.role not in {UserRole.ADMIN, UserRole.SUPERADMIN}:
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    business = await BusinessesRepo(session).get_singleton()
    if business is None:
        await callback.answer("Сервис недоступен", show_alert=True)
        return

    try:
        await BookingService(session).cancel_booking(
            business=business,
            actor_user_id=actor.id,
            actor_role=actor.role,
            booking_id=booking_id,
        )
    except NotFound:
        await callback.answer("Запись не найдена", show_alert=True)
        return
    except CannotCancelInCurrentStatus:
        await callback.answer("Запись уже отменена или завершена", show_alert=True)
        return
    except (Forbidden, CancellationTooLate):
        # Forbidden shouldn't reach here (we checked role). CancellationTooLate
        # shouldn't either (admin bypasses the window). Still defensive.
        await callback.answer("Операция запрещена", show_alert=True)
        return

    # Dispatch the cancellation notifications synchronously (same pattern as
    # /api/v1/admin/bookings/{id}/cancel). Failure must not prevent the callback
    # answer below.
    try:
        await NotificationService(session, bot).dispatch_pending_for_booking(booking_id)
    except Exception:
        log.exception("admin_callback.dispatch_failed", booking_id=booking_id)

    # Edit original message to reflect cancellation
    try:
        if isinstance(callback.message, Message):
            await callback.message.edit_text(
                "❌ <b>Запись отменена администратором</b>", reply_markup=None
            )
    except TelegramBadRequest:
        # Original message may be too old to edit; fail silently
        pass

    await callback.answer("Запись отменена", show_alert=False)
