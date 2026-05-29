from datetime import UTC, datetime, timedelta
from typing import Any

import jwt as pyjwt

from app.core.errors import InvalidToken


def issue_jwt(
    *,
    subject: str,
    role: str,
    secret: str,
    algorithm: str,
    expires_in: timedelta,
    issued_at: datetime | None = None,
) -> str:
    now = issued_at or datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_in).timestamp()),
    }
    return pyjwt.encode(payload, secret, algorithm=algorithm)


def issue_download_ticket(
    *,
    subject: str,
    role: str,
    kind: str,
    params: dict[str, Any],
    secret: str,
    algorithm: str,
    expires_in: timedelta = timedelta(seconds=60),
    issued_at: datetime | None = None,
) -> str:
    """Short-lived, single-purpose JWT for file downloads opened in an external
    browser (Telegram WebApp.openLink can't attach Authorization headers).

    Scope: only `purpose=export` tokens are accepted by export endpoints — even
    leaking the URL via logs/Referer cannot reuse this ticket for a regular API
    call. Default TTL 60s caps the blast radius.
    """
    now = issued_at or datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "purpose": "export",
        "kind": kind,
        "params": params,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_in).timestamp()),
    }
    return pyjwt.encode(payload, secret, algorithm=algorithm)


def decode_jwt(token: str, *, secret: str, algorithm: str) -> dict[str, Any]:
    try:
        return pyjwt.decode(token, secret, algorithms=[algorithm])
    except pyjwt.ExpiredSignatureError as exc:
        raise InvalidToken("Token expired") from exc
    except pyjwt.InvalidTokenError as exc:
        raise InvalidToken("Token invalid") from exc
