"""Root conftest: set required env vars before any app module is imported."""

import os

# Provide minimal required settings for all tests.
# These fallbacks are applied only when the env var isn't already set.
# pydantic-settings precedence: os.environ > .env file > defaults, so a real
# env var (or one set above by the test runner) will be used instead of these.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://booking:booking@localhost:5432/booking")
os.environ.setdefault(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://booking:booking@localhost:5432/booking_test",
)
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-do-not-use-in-prod")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_DEBUG", "true")
