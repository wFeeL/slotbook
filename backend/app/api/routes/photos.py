from __future__ import annotations

import asyncio
import time

import httpx
from fastapi import APIRouter, Request, Response

from app.api.deps import SessionDep
from app.core.config import get_settings
from app.core.errors import NotFound
from app.db.models.photo import Photo

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


@router.get("/{photo_id}")
async def proxy_photo(
    photo_id: int, session: SessionDep, request: Request
) -> Response:
    photo = await session.get(Photo, photo_id)
    if photo is None:
        raise NotFound("Photo not found")

    bot = request.app.state.bot
    settings = get_settings()

    file_path = await _resolve_file_path(bot, photo.telegram_file_id)
    url = f"https://api.telegram.org/file/bot{settings.BOT_TOKEN}/{file_path}"
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            r = await client.get(url)
            if r.status_code == 404:
                _CACHE.pop(photo.telegram_file_id, None)
                file_path = await _resolve_file_path(bot, photo.telegram_file_id)
                url = (
                    f"https://api.telegram.org/file/bot{settings.BOT_TOKEN}/{file_path}"
                )
                r = await client.get(url)
            r.raise_for_status()
        except httpx.HTTPError as exc:
            return Response(
                content=f"Upstream fetch failed: {exc}", status_code=502
            )

    return Response(
        content=r.content,
        media_type=photo.mime_type or "image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )
