from enum import StrEnum
from functools import lru_cache
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    EnvSettingsSource,
    SettingsConfigDict,
)


class BotMode(StrEnum):
    POLLING = "polling"
    WEBHOOK = "webhook"


class _CommaSepBypassMixin:
    """Mixin that passes comma-separated strings through unparsed so field_validator can handle them."""

    def prepare_field_value(
        self, field_name: str, field: Any, value: Any, value_is_complex: bool
    ) -> Any:
        if field_name == "BOT_ADMIN_TELEGRAM_IDS" and isinstance(value, str):
            # Return the raw string so field_validator can process it.
            return value
        return super().prepare_field_value(field_name, field, value, value_is_complex)  # type: ignore[misc]


class _CommaSeparatedEnvSource(_CommaSepBypassMixin, EnvSettingsSource):
    """Custom os.environ source that handles comma-separated values for list fields."""


class _CommaSeparatedDotEnvSource(_CommaSepBypassMixin, DotEnvSettingsSource):
    """Custom .env-file source that handles comma-separated values for list fields."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_ENV: Literal["local", "test", "prod"] = "local"
    APP_DEBUG: bool = True

    DATABASE_URL: str
    TEST_DATABASE_URL: str | None = None

    BOT_TOKEN: str = "missing"
    BOT_USERNAME: str | None = None  # e.g. "slotbook_bot" — used for invite link generation
    BOT_ADMIN_TELEGRAM_IDS: list[int] = Field(default_factory=list)
    BOT_MODE: BotMode = BotMode.POLLING
    BOT_WEBHOOK_URL: str | None = None
    BOT_WEBHOOK_SECRET_TOKEN: str | None = None
    BOT_WEBHOOK_PORT: int = 8001
    MINI_APP_URL: str = "https://miniapp.example.com"
    BOT_ADMIN_NOTIFY_LIMIT: int = 10

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    BUSINESS_NAME: str = "Demo Studio"
    BUSINESS_TIMEZONE: str = "Europe/Moscow"
    BUSINESS_BOOKING_BUFFER_MINUTES: int = 0
    BUSINESS_MIN_CANCELLATION_HOURS: int = 2
    BUSINESS_SLOT_STEP_MINUTES: int = 15

    # Worker
    WORKER_TICK_SECONDS: int = 60

    @field_validator("BOT_ADMIN_TELEGRAM_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: Any) -> list[int]:
        """Accept either a comma-separated string or a list."""
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            return [int(item) for item in v.split(",") if item.strip()]
        if isinstance(v, list):
            return [int(item) for item in v]
        msg = f"Cannot parse BOT_ADMIN_TELEGRAM_IDS from {type(v)}"
        raise ValueError(msg)

    @model_validator(mode="after")
    def _check_prod_secrets(self) -> "Settings":
        if self.APP_ENV == "prod":
            if self.BOT_TOKEN == "missing":
                raise ValueError("BOT_TOKEN must be set in production")
            if self.JWT_SECRET in {"change_me", "change_me_in_real_env"}:
                raise ValueError("JWT_SECRET must be set to a real value in production")
            if len(self.JWT_SECRET) < 32:
                raise ValueError("JWT_SECRET must be at least 32 chars in prod")
            if self.BOT_MODE != BotMode.WEBHOOK:
                raise ValueError("BOT_MODE must be 'webhook' in production")
            if not self.BOT_WEBHOOK_URL or not self.BOT_WEBHOOK_URL.startswith("https://"):
                raise ValueError("BOT_WEBHOOK_URL must be a non-empty HTTPS URL in production")
            if not self.BOT_WEBHOOK_SECRET_TOKEN:
                raise ValueError("BOT_WEBHOOK_SECRET_TOKEN must be set in production")
            if "example.com" in self.MINI_APP_URL or not self.MINI_APP_URL.startswith("https://"):
                raise ValueError("MINI_APP_URL must be a real HTTPS URL in production")
        return self

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: Any,
        env_settings: Any,
        dotenv_settings: Any,
        file_secret_settings: Any,
    ) -> tuple[Any, ...]:
        return (
            init_settings,
            _CommaSeparatedEnvSource(settings_cls),
            _CommaSeparatedDotEnvSource(settings_cls),
            file_secret_settings,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
