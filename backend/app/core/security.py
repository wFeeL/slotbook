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


def decode_jwt(token: str, *, secret: str, algorithm: str) -> dict[str, Any]:
    try:
        return pyjwt.decode(token, secret, algorithms=[algorithm])
    except pyjwt.ExpiredSignatureError as exc:
        raise InvalidToken("Token expired") from exc
    except pyjwt.InvalidTokenError as exc:
        raise InvalidToken("Token invalid") from exc
