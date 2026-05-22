"""Root conftest: set required env vars before any app module is imported."""

import os

# Provide minimal required settings for all tests.
# These are overridden by .env if it exists (env vars take precedence over file).
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://booking:booking@localhost:5432/booking")
os.environ.setdefault(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://booking:booking@localhost:5432/booking_test",
)
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-do-not-use-in-prod")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_DEBUG", "true")
