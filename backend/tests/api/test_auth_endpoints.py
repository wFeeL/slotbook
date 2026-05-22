from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest
from httpx import AsyncClient

from app.core.config import Settings, get_settings


def _build_init_data(bot_token: str, user: dict[str, object]) -> str:
    fields = {
        "auth_date": str(int(time.time())),
        "query_id": "AAA",
        "user": json.dumps(user, separators=(",", ":")),
    }
    dcs = "\n".join(f"{k}={fields[k]}" for k in sorted(fields))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret_key, dcs.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


@pytest.mark.asyncio
async def test_auth_telegram_creates_user_and_returns_token(
    client: AsyncClient, settings: Settings
) -> None:
    init = _build_init_data(settings.BOT_TOKEN, {"id": 9001, "first_name": "Test"})
    response = await client.post("/api/v1/auth/telegram", json={"init_data": init})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["telegram_id"] == 9001
    assert body["user"]["role"] == "client"


@pytest.mark.asyncio
async def test_auth_telegram_promotes_admin_from_env(
    client: AsyncClient, settings: Settings
) -> None:
    """User with telegram_id in BOT_ADMIN_TELEGRAM_IDS gets role=admin on creation.

    We use dependency_overrides to inject a Settings object that has 9002 in
    BOT_ADMIN_TELEGRAM_IDS, avoiding any interaction with the lru_cache on get_settings.
    """
    base = get_settings()
    admin_settings = Settings(**(base.model_dump() | {"BOT_ADMIN_TELEGRAM_IDS": [9002]}))

    def _override_settings() -> Settings:
        return admin_settings

    # Access the FastAPI app through the ASGI transport layer
    app = client._transport.app  # type: ignore[attr-defined]
    app.dependency_overrides[get_settings] = _override_settings
    try:
        init = _build_init_data(settings.BOT_TOKEN, {"id": 9002, "first_name": "Boss"})
        response = await client.post("/api/v1/auth/telegram", json={"init_data": init})
        assert response.status_code == 200
        assert response.json()["user"]["role"] == "admin"
    finally:
        app.dependency_overrides.pop(get_settings, None)


@pytest.mark.asyncio
async def test_auth_telegram_rejects_tampered_hash(client: AsyncClient, settings: Settings) -> None:
    init = _build_init_data(settings.BOT_TOKEN, {"id": 9003, "first_name": "X"})
    tampered = init[:-1] + ("0" if init[-1] != "0" else "1")
    response = await client.post("/api/v1/auth/telegram", json={"init_data": tampered})
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "invalid_init_data"
