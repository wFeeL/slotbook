import pathlib

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


def test_dotenv_file_parses_comma_separated_admin_ids(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("BOT_ADMIN_TELEGRAM_IDS", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DATABASE_URL=postgresql+asyncpg://x/y\nJWT_SECRET=x\nBOT_ADMIN_TELEGRAM_IDS=11,22,33\n"
    )

    from app.core.config import Settings

    class _S(Settings):
        model_config = Settings.model_config | {"env_file": str(env_file)}

    s = _S()
    assert s.BOT_ADMIN_TELEGRAM_IDS == [11, 22, 33]
