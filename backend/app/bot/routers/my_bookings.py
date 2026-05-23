from __future__ import annotations

from datetime import UTC, datetime
from html import escape as _html_escape

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import my_bookings_keyboard
from app.bot.texts import _fmt_dt
from app.core.config import get_settings
from app.db.repositories.bookings import BookingsRepo
from app.db.repositories.businesses import BusinessesRepo
from app.db.repositories.services import ServicesRepo
from app.db.repositories.users import UsersRepo

router = Router(name="my_bookings")


@router.message(Command("my_bookings"))
async def handle_my_bookings(message: Message, session: AsyncSession) -> None:
    settings = get_settings()
    if message.from_user is None:
        return
    user = await UsersRepo(session).get_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer("Вы не зарегистрированы. Отправьте /start.")
        return

    business = await BusinessesRepo(session).get_singleton()
    assert business is not None  # bootstrapped at API startup

    bookings = await BookingsRepo(session).list_for_client_upcoming(
        user.id, now_utc=datetime.now(UTC), limit=5
    )

    if not bookings:
        await message.answer(
            "У вас пока нет активных записей.",  # noqa: RUF001
            reply_markup=my_bookings_keyboard(settings.MINI_APP_URL),
        )
        return

    lines = ["<b>Ваши ближайшие записи:</b>\n"]
    for b in bookings:
        svc = await ServicesRepo(session).get(b.service_id)
        title = _html_escape(svc.title) if svc else "?"
        lines.append(f"• {_fmt_dt(b.starts_at, business.timezone)} — {title}")

    await message.answer("\n".join(lines), reply_markup=my_bookings_keyboard(settings.MINI_APP_URL))
