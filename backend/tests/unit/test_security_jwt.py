from datetime import timedelta

import pytest

from app.core.errors import InvalidToken
from app.core.security import decode_jwt, issue_jwt


def test_jwt_roundtrip() -> None:
    token = issue_jwt(
        subject="42",
        role="client",
        secret="s",
        algorithm="HS256",
        expires_in=timedelta(minutes=10),
    )
    payload = decode_jwt(token, secret="s", algorithm="HS256")
    assert payload["sub"] == "42"
    assert payload["role"] == "client"


def test_jwt_rejects_tampered_signature() -> None:
    token = issue_jwt(
        subject="42",
        role="client",
        secret="s",
        algorithm="HS256",
        expires_in=timedelta(minutes=10),
    )
    header, payload, signature = token.split(".")
    # Flip a middle byte (avoid the last char which only carries 4 meaningful bits
    # and can silently collide when base64url-decoded with a neighbouring char)
    mid = len(signature) // 2
    flipped = signature[:mid] + ("A" if signature[mid] != "A" else "B") + signature[mid + 1 :]
    tampered = f"{header}.{payload}.{flipped}"
    with pytest.raises(InvalidToken):
        decode_jwt(tampered, secret="s", algorithm="HS256")


def test_jwt_rejects_expired_token() -> None:
    token = issue_jwt(
        subject="42",
        role="client",
        secret="s",
        algorithm="HS256",
        expires_in=timedelta(seconds=-1),
    )
    with pytest.raises(InvalidToken):
        decode_jwt(token, secret="s", algorithm="HS256")


def test_jwt_rejects_wrong_secret() -> None:
    token = issue_jwt(
        subject="42",
        role="client",
        secret="s1",
        algorithm="HS256",
        expires_in=timedelta(minutes=10),
    )
    with pytest.raises(InvalidToken):
        decode_jwt(token, secret="s2", algorithm="HS256")
