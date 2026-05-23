from __future__ import annotations

from html import escape as _html_escape

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import main_menu_keyboard
from app.core.config import get_settings
from app.db.repositories.users import UsersRepo

router = Router(name="start")


@router.message(CommandStart())
async def handle_start(message: Message, session: AsyncSession) -> None:
    settings = get_settings()
    user = message.from_user
    if user is None:
        return  # ignore updates without an originating user (channels etc.)

    await UsersRepo(session).upsert_from_telegram(
        telegram_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        admin_telegram_ids=set(),  # admin promotion stays exclusive to /auth/telegram
    )

    text = (
        f"Привет, {_html_escape(user.first_name or 'друг')}! 👋\n\n"
        "Здесь можно записаться на услугу, посмотреть свои записи или связаться с администратором."  # noqa: RUF001
    )
    await message.answer(text, reply_markup=main_menu_keyboard(settings.MINI_APP_URL))
