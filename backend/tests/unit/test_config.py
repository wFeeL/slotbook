import pytest

from app.core.config import get_settings


def test_bot_admin_telegram_ids_comma_separated(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_ADMIN_TELEGRAM_IDS", "1,2,3")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/db")
    monkeypatch.setenv("JWT_SECRET", "testsecret")
    get_settings.cache_clear()
    try:
        settings = get_settings()
        assert settings.BOT_ADMIN_TELEGRAM_IDS == [1, 2, 3]
    finally:
        get_settings.cache_clear()


def test_bot_admin_telegram_ids_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_ADMIN_TELEGRAM_IDS", "")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/db")
    monkeypatch.setenv("JWT_SECRET", "testsecret")
    get_settings.cache_clear()
    try:
        settings = get_settings()
        assert settings.BOT_ADMIN_TELEGRAM_IDS == []
    finally:
        get_settings.cache_clear()


def test_bot_admin_telegram_ids_with_spaces(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_ADMIN_TELEGRAM_IDS", " 10 , 20 , 30 ")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/db")
    monkeypatch.setenv("JWT_SECRET", "testsecret")
    get_settings.cache_clear()
    try:
        settings = get_settings()
        assert settings.BOT_ADMIN_TELEGRAM_IDS == [10, 20, 30]
    finally:
        get_settings.cache_clear()
