from __future__ import annotations

from datetime import UTC, datetime
from html import escape as _html_escape

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import main_menu_keyboard
from app.core.config import get_settings
from app.db.enums import UserRole
from app.db.repositories.admin_invites import AdminInvitesRepo
from app.db.repositories.users import UsersRepo

router = Router(name="start")


@router.message(CommandStart())
async def handle_start(message: Message, session: AsyncSession) -> None:
    settings = get_settings()
    user = message.from_user
    if user is None:
        return  # ignore updates without an originating user (channels etc.)

    # Parse /start payload (deep-link arg).
    text = (message.text or "").strip()
    parts = text.split(maxsplit=1)
    # Cap payload length defensively — Telegram's deep-link spec allows up to 64
    # characters; anything longer is malformed or an abuse attempt. Avoids
    # oversized DB lookups on hostile input.
    payload = (parts[1] if len(parts) > 1 else "")[:64]

    invite_token: str | None = None
    if payload.startswith("invite_"):
        invite_token = payload[len("invite_") :]

    db_user = await UsersRepo(session).upsert_from_telegram(
        telegram_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        admin_telegram_ids=set(),  # admin promotion stays exclusive to /auth/telegram
    )

    promoted_to: str | None = None
    if invite_token:
        repo = AdminInvitesRepo(session)
        invite = await repo.get_by_token(invite_token)
        now = datetime.now(UTC)
        if invite is None:
            await message.answer("⚠️ Ссылка-приглашение недействительна.")
            return
        if invite.consumed_at is not None:
            await message.answer("⚠️ Эта ссылка уже была использована.")
            return
        if invite.expires_at <= now:
            await message.answer("⚠️ Срок действия ссылки истёк.")
            return

        target_role = UserRole(invite.role)
        # Don't downgrade superadmins.
        if db_user.role != UserRole.SUPERADMIN:
            db_user.role = target_role
        await repo.consume(invite, db_user.id)
        await session.flush()
        promoted_to = invite.role

    if promoted_to:
        text_msg = (
            f"🎉 Вы стали "
            f"{'администратором' if promoted_to == 'admin' else 'сотрудником'} SlotBook!\n\n"
            "Откройте Mini App ниже, чтобы перейти в панель."
        )
    else:
        text_msg = (
            f"Привет, {_html_escape(user.first_name or 'друг')}! 👋\n\n"
            "Здесь можно записаться на услугу, посмотреть свои записи или связаться с администратором."
        )
    await message.answer(text_msg, reply_markup=main_menu_keyboard(settings.MINI_APP_URL))
