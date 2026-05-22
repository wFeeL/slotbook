from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    Chat,
    Message,
    Update,
)
from aiogram.types import (
    User as TgUser,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bot.middlewares.db import DbSessionMiddleware
from app.bot.middlewares.logging import UpdateLoggingMiddleware
from app.bot.routers import admin_callbacks, help, my_bookings, start


@pytest.fixture
def mock_bot() -> Bot:
    """Bot instance with all I/O methods replaced by AsyncMock."""
    bot = AsyncMock(spec=Bot)
    bot.id = 999
    return bot


class _TestDbSessionMiddleware(DbSessionMiddleware):
    """Injects a specific sessionmaker, used in tests to bind to db_engine."""

    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker

    async def __call__(self, handler, event, data):  # type: ignore[no-untyped-def]
        async with self._sessionmaker() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise


@pytest_asyncio.fixture
async def dispatcher(db_engine):  # type: ignore[no-untyped-def]
    """Dispatcher wired to the test DB. mock_bot is injected at feed time."""
    sessionmaker = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.outer_middleware(UpdateLoggingMiddleware())
    dp.update.outer_middleware(_TestDbSessionMiddleware(sessionmaker))
    # Each router module holds a singleton Router; reset parent so it can be
    # re-attached to a fresh Dispatcher each test (function scope).
    for r in (start.router, help.router, my_bookings.router, admin_callbacks.router):
        r._parent_router = None  # type: ignore[attr-defined]
    dp.include_router(start.router)
    dp.include_router(help.router)
    dp.include_router(my_bookings.router)
    dp.include_router(admin_callbacks.router)
    return dp


def make_message_update(
    text: str,
    *,
    update_id: int = 1,
    from_user_id: int,
    from_user_first_name: str = "Test",
    from_user_username: str | None = None,
    chat_id: int | None = None,
) -> Update:
    user = TgUser(
        id=from_user_id, is_bot=False, first_name=from_user_first_name, username=from_user_username
    )
    chat = Chat(id=chat_id or from_user_id, type="private")
    message = Message(
        message_id=update_id * 10,
        date=datetime.now(UTC),
        chat=chat,
        from_user=user,
        text=text,
    )
    return Update(update_id=update_id, message=message)


def make_callback_update(
    data: str,
    *,
    update_id: int = 1,
    from_user_id: int,
    message_id: int = 100,
    chat_id: int | None = None,
) -> Update:
    user = TgUser(id=from_user_id, is_bot=False, first_name="Admin")
    chat = Chat(id=chat_id or from_user_id, type="private")
    original_message = Message(
        message_id=message_id,
        date=datetime.now(UTC),
        chat=chat,
        from_user=TgUser(id=999, is_bot=True, first_name="Bot"),
        text="Original message",
    )
    cb = CallbackQuery(
        id=str(update_id),
        from_user=user,
        chat_instance="test-chat-instance",
        data=data,
        message=original_message,
    )
    return Update(update_id=update_id, callback_query=cb)


@pytest_asyncio.fixture
async def feed(dispatcher: Dispatcher, mock_bot: Bot):  # type: ignore[no-untyped-def]
    """Helper coroutine for tests to feed an Update through the dispatcher."""

    async def _feed(update: Update) -> None:
        await dispatcher.feed_update(mock_bot, update)

    return _feed
