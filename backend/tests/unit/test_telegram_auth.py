import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest

from app.core.errors import InitDataExpired, InvalidInitData
from app.core.telegram_auth import validate_init_data


def _make_init_data(bot_token: str, user: dict[str, object], auth_date: int) -> str:
    fields = {
        "auth_date": str(auth_date),
        "query_id": "AAA",
        "user": json.dumps(user, separators=(",", ":")),
    }
    data_check_string = "\n".join(f"{k}={fields[k]}" for k in sorted(fields))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    fields["hash"] = computed_hash
    return urlencode(fields)


def test_validates_correct_init_data() -> None:
    user = {"id": 12345, "first_name": "Иван", "last_name": "П", "username": "ivan"}
    init = _make_init_data("BOT_TOKEN", user, int(time.time()))
    payload = validate_init_data("BOT_TOKEN", init, max_age_seconds=86400)
    assert payload.telegram_id == 12345
    assert payload.first_name == "Иван"
    assert payload.username == "ivan"


def test_rejects_tampered_hash() -> None:
    user = {"id": 12345, "first_name": "Ivan"}
    init = _make_init_data("BOT_TOKEN", user, int(time.time()))
    # Flip the last hex character of the hash
    if "hash=" in init:
        before, after = init.rsplit("hash=", 1)
        last = after[-1]
        new_last = "0" if last != "0" else "1"
        tampered = before + "hash=" + after[:-1] + new_last
    else:
        tampered = init + "0"
    with pytest.raises(InvalidInitData):
        validate_init_data("BOT_TOKEN", tampered, max_age_seconds=86400)


def test_rejects_wrong_token() -> None:
    user = {"id": 12345, "first_name": "Ivan"}
    init = _make_init_data("BOT_TOKEN", user, int(time.time()))
    with pytest.raises(InvalidInitData):
        validate_init_data("OTHER_TOKEN", init, max_age_seconds=86400)


def test_rejects_expired_auth_date() -> None:
    user = {"id": 12345, "first_name": "Ivan"}
    init = _make_init_data("BOT_TOKEN", user, int(time.time()) - 100_000)
    with pytest.raises(InitDataExpired):
        validate_init_data("BOT_TOKEN", init, max_age_seconds=86400)


def test_rejects_missing_user_field() -> None:
    # Build a properly-signed initData without the 'user' field so validation
    # passes the hash check and actually exercises the missing-user-field guard.
    bot_token = "BOT_TOKEN"
    fields = {
        "auth_date": str(int(time.time())),
        "query_id": "AAA",
    }
    data_check_string = "\n".join(f"{k}={fields[k]}" for k in sorted(fields))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    with pytest.raises(InvalidInitData):
        validate_init_data(bot_token, urlencode(fields), max_age_seconds=86400)
