from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update

log = structlog.get_logger()


def _summary(event: TelegramObject) -> dict[str, Any]:
    if isinstance(event, Update):
        if event.message:
            return _summary(event.message)
        if event.callback_query:
            return _summary(event.callback_query)
        return {"update_id": event.update_id}
    if isinstance(event, Message):
        return {
            "kind": "message",
            "telegram_id": event.from_user.id if event.from_user else None,
            "text": (event.text or "")[:100],
        }
    if isinstance(event, CallbackQuery):
        return {
            "kind": "callback_query",
            "telegram_id": event.from_user.id if event.from_user else None,
            "data": event.data,
        }
    return {"kind": type(event).__name__}


class UpdateLoggingMiddleware(BaseMiddleware):
    """Logs every incoming update with its summary."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        log.info("bot.update", **_summary(event))
        try:
            return await handler(event, data)
        except Exception as exc:
            log.warning("bot.update_failed", error=str(exc), **_summary(event))
            raise
