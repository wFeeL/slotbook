from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl

from app.core.errors import InitDataExpired, InvalidInitData


@dataclass(frozen=True, slots=True)
class InitDataPayload:
    telegram_id: int
    first_name: str | None
    last_name: str | None
    username: str | None
    auth_date: int


def _data_check_string(pairs: list[tuple[str, str]]) -> str:
    filtered = [(k, v) for k, v in pairs if k != "hash"]
    filtered.sort(key=lambda kv: kv[0])
    return "\n".join(f"{k}={v}" for k, v in filtered)


def _compute_hash(bot_token: str, data_check_string: str) -> str:
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    return hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()


def validate_init_data(
    bot_token: str,
    init_data_raw: str,
    *,
    max_age_seconds: int = 86400,
    now: float | None = None,
) -> InitDataPayload:
    if not init_data_raw:
        raise InvalidInitData("Empty initData")

    pairs = parse_qsl(init_data_raw, strict_parsing=False, keep_blank_values=True)
    fields = dict(pairs)

    received_hash = fields.get("hash")
    if not received_hash:
        raise InvalidInitData("Missing hash")

    expected = _compute_hash(bot_token, _data_check_string(pairs))
    if not hmac.compare_digest(expected, received_hash):
        raise InvalidInitData("Hash mismatch")

    auth_date_raw = fields.get("auth_date")
    if not auth_date_raw:
        raise InvalidInitData("Missing auth_date")
    try:
        auth_date = int(auth_date_raw)
    except ValueError as exc:
        raise InvalidInitData("Invalid auth_date") from exc

    current = now if now is not None else time.time()
    if current - auth_date > max_age_seconds:
        raise InitDataExpired("auth_date too old")

    user_raw = fields.get("user")
    if not user_raw:
        raise InvalidInitData("Missing user field")
    try:
        user_obj = json.loads(user_raw)
    except json.JSONDecodeError as exc:
        raise InvalidInitData("Malformed user field") from exc

    if "id" not in user_obj:
        raise InvalidInitData("user.id missing")

    return InitDataPayload(
        telegram_id=int(user_obj["id"]),
        first_name=user_obj.get("first_name"),
        last_name=user_obj.get("last_name"),
        username=user_obj.get("username"),
        auth_date=auth_date,
    )
