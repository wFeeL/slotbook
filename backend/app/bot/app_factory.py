from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.core.config import Settings


def create_bot(settings: Settings) -> Bot:
    """Build a Bot instance. Safe to call from API process (no dispatcher needed)."""
    return Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher(_settings: Settings) -> Dispatcher:
    """Build a Dispatcher with all routers and middlewares.

    Routers are imported here (not at module top) to avoid circular imports
    when the API process imports app_factory without needing the dispatcher.
    """
    from app.bot.middlewares.db import DbSessionMiddleware
    from app.bot.middlewares.logging import UpdateLoggingMiddleware
    from app.bot.routers import admin_callbacks, help, my_bookings, start, upload

    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.update.outer_middleware(UpdateLoggingMiddleware())
    dispatcher.update.outer_middleware(DbSessionMiddleware())

    dispatcher.include_router(start.router)
    dispatcher.include_router(upload.router)
    dispatcher.include_router(help.router)
    dispatcher.include_router(my_bookings.router)
    dispatcher.include_router(admin_callbacks.router)

    return dispatcher
