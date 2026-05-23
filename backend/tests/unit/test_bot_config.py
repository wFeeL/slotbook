import pytest

from app.core.config import BotMode, Settings

_PROD_GRADE_SECRET = "a" * 32  # meets the >=32 chars production requirement


def _base_kwargs(**overrides) -> dict:
    kw = {
        "APP_ENV": "test",
        "DATABASE_URL": "postgresql+asyncpg://test/test",
        "JWT_SECRET": _PROD_GRADE_SECRET,
        "BOT_TOKEN": "test-token",
        "MINI_APP_URL": "https://miniapp.example.com",
    }
    kw.update(overrides)
    return kw


def test_defaults_match_dev_polling() -> None:
    s = Settings(**_base_kwargs())
    assert s.BOT_MODE == BotMode.POLLING
    assert s.BOT_WEBHOOK_PORT == 8001
    assert s.BOT_ADMIN_NOTIFY_LIMIT == 10


def test_prod_requires_webhook_mode() -> None:
    with pytest.raises(ValueError, match="BOT_MODE must be 'webhook'"):
        Settings(**_base_kwargs(APP_ENV="prod"))


def test_prod_requires_webhook_secret_and_url() -> None:
    with pytest.raises(ValueError, match="BOT_WEBHOOK_URL"):
        Settings(
            **_base_kwargs(
                APP_ENV="prod",
                BOT_MODE="webhook",
                MINI_APP_URL="https://real.example/miniapp",  # passes the example.com check below
            )
        )


def test_prod_requires_real_mini_app_url() -> None:
    with pytest.raises(ValueError, match="MINI_APP_URL"):
        Settings(
            **_base_kwargs(
                APP_ENV="prod",
                BOT_MODE="webhook",
                BOT_WEBHOOK_URL="https://bot.example/webhook",
                BOT_WEBHOOK_SECRET_TOKEN="s3cret",
                # MINI_APP_URL uses the example.com default → must fail
            )
        )


def test_prod_passes_when_fully_configured() -> None:
    s = Settings(
        **_base_kwargs(
            APP_ENV="prod",
            BOT_MODE="webhook",
            BOT_WEBHOOK_URL="https://bot.real.com/webhook",
            BOT_WEBHOOK_SECRET_TOKEN="s3cret",
            MINI_APP_URL="https://app.real.com",
        )
    )
    assert s.BOT_MODE == BotMode.WEBHOOK


def test_prod_rejects_short_jwt_secret() -> None:
    with pytest.raises(ValueError, match="JWT_SECRET must be at least 32 chars"):
        Settings(
            **_base_kwargs(
                APP_ENV="prod",
                BOT_MODE="webhook",
                BOT_WEBHOOK_URL="https://bot.real.com/webhook",
                BOT_WEBHOOK_SECRET_TOKEN="s3cret",
                MINI_APP_URL="https://app.real.com",
                JWT_SECRET="x" * 16,  # too short
            )
        )
