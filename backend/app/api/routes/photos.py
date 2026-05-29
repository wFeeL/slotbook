from __future__ import annotations

import asyncio
import logging
import time

import httpx
from aiogram.exceptions import TelegramAPIError
from fastapi import APIRouter, Request, Response

from app.api.deps import SessionDep
from app.core.config import get_settings
from app.core.errors import NotFound
from app.db.models.photo import Photo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/photos", tags=["photos"])

_CACHE: dict[str, tuple[str, float]] = {}
_TTL_SECONDS = 3600
_CACHE_LOCK = asyncio.Lock()


async def _resolve_file_path(bot, file_id: str) -> str:
    now = time.monotonic()
    cached = _CACHE.get(file_id)
    if cached is not None and now - cached[1] < _TTL_SECONDS:
        return cached[0]
    async with _CACHE_LOCK:
        cached = _CACHE.get(file_id)
        if cached is not None and now - cached[1] < _TTL_SECONDS:
            return cached[0]
        file = await bot.get_file(file_id)
        _CACHE[file_id] = (file.file_path, now)
        return file.file_path


def _bad_gateway(photo_id: int, reason: str) -> Response:
    # `reason` may contain the upstream URL with the embedded bot token (httpx
    # error variants include the full URL in their str representation). Keep
    # details in the server log only — never echo to the response body.
    logger.warning("photo.proxy_upstream_failed photo_id=%s reason=%s", photo_id, reason)
    return Response(content="Upstream fetch failed", status_code=502)


@router.get("/{photo_id}")
async def proxy_photo(
    photo_id: int, session: SessionDep, request: Request
) -> Response:
    photo = await session.get(Photo, photo_id)
    if photo is None:
        raise NotFound("Photo not found")

    bot = request.app.state.bot
    settings = get_settings()

    try:
        file_path = await _resolve_file_path(bot, photo.telegram_file_id)
    except TelegramAPIError as exc:
        return _bad_gateway(photo_id, f"get_file: {exc}")

    url = f"https://api.telegram.org/file/bot{settings.BOT_TOKEN}/{file_path}"
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            r = await client.get(url)
            if r.status_code == 404:
                _CACHE.pop(photo.telegram_file_id, None)
                try:
                    file_path = await _resolve_file_path(bot, photo.telegram_file_id)
                except TelegramAPIError as exc:
                    return _bad_gateway(photo_id, f"get_file (retry): {exc}")
                url = (
                    f"https://api.telegram.org/file/bot{settings.BOT_TOKEN}/{file_path}"
                )
                r = await client.get(url)
            r.raise_for_status()
        except httpx.HTTPError as exc:
            return _bad_gateway(photo_id, f"httpx: {exc}")

    return Response(
        content=r.content,
        media_type=photo.mime_type or "image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )
