from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="help")

HELP_TEXT = (
    "<b>SlotBook</b> — система онлайн-записи через Telegram.\n\n"
    "<b>Команды:</b>\n"
    "/start — открыть главное меню\n"
    "/my_bookings — мои записи\n"
    "/help — эта справка\n\n"
    "Записаться, перенести или отменить запись можно через Mini App "
    "по кнопке «Записаться» в главном меню."
)


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    await message.answer(HELP_TEXT)
