from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings, get_settings
from app.core.security import issue_jwt
from app.db.base import Base
from app.db.enums import UserRole
from app.db.models.branch import Branch
from app.db.models.business import Business
from app.db.models.user import User
from app.db.session import get_session

# Force settings to load test DB URL.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_DEBUG", "false")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("BOT_TOKEN", "test-bot-token")
os.environ.setdefault("BUSINESS_NAME", "Test Studio")
os.environ.setdefault("BUSINESS_TIMEZONE", "UTC")


def _resolve_test_db_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        raise RuntimeError(
            "TEST_DATABASE_URL is not set. Start Postgres via docker compose and export the URL "
            "(e.g. postgresql+asyncpg://booking:booking@localhost:5432/booking_test)."
        )
    return url


@pytest.fixture(scope="session")
def event_loop():  # type: ignore[no-untyped-def]
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_engine():  # type: ignore[no-untyped-def]
    url = _resolve_test_db_url()
    engine = create_async_engine(url, future=True)
    async with engine.begin() as conn:
        # Drop tables first, then drop the enum types if they exist.
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text("DROP TYPE IF EXISTS user_role"))
        await conn.execute(text("DROP TYPE IF EXISTS schedule_exception_type"))
        await conn.execute(text("DROP TYPE IF EXISTS booking_status"))
        await conn.execute(text("DROP TYPE IF EXISTS booking_source"))
        await conn.execute(text("DROP TYPE IF EXISTS notification_type"))
        await conn.execute(text("DROP TYPE IF EXISTS notification_status"))
        # Create the enum types before creating tables (create_type=False on the ORM models).
        await conn.execute(
            text("CREATE TYPE user_role AS ENUM ('client','admin','staff','superadmin')")
        )
        await conn.execute(
            text(
                "CREATE TYPE schedule_exception_type"
                " AS ENUM ('day_off','extra_working_time','blocked_time')"
            )
        )
        await conn.execute(
            text(
                "CREATE TYPE booking_status AS ENUM ("
                "'pending','confirmed','cancelled_by_client','cancelled_by_admin',"
                "'completed','no_show','rescheduled')"
            )
        )
        await conn.execute(
            text("CREATE TYPE booking_source AS ENUM ('mini_app','bot','admin_manual')")
        )
        await conn.execute(
            text(
                "CREATE TYPE notification_type AS ENUM ("
                "'booking_created_client','booking_created_admin',"
                "'reminder_24h','reminder_2h',"
                "'booking_cancelled_client','booking_cancelled_admin',"
                "'booking_rescheduled_client','booking_rescheduled_admin')"
            )
        )
        await conn.execute(
            text("CREATE TYPE notification_status AS ENUM ('pending','sent','failed')")
        )
        await conn.run_sync(Base.metadata.create_all)
        # Replace the non-unique partial index (created by ORM) with a UNIQUE one for race safety.
        await conn.execute(text("DROP INDEX IF EXISTS bookings_active_by_staff"))
        await conn.execute(
            text(
                "CREATE UNIQUE INDEX bookings_active_by_staff ON bookings (staff_id, starts_at) "
                "WHERE status IN ('pending', 'confirmed')"
            )
        )
        # Apply the EXCLUDE constraint that mirrors alembic migration 0009 so race
        # tests that depend on it see the same behaviour as production.
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
        await conn.execute(
            text(
                "ALTER TABLE bookings ADD CONSTRAINT bookings_no_overlap "
                "EXCLUDE USING gist ("
                "staff_id WITH =, tstzrange(starts_at, ends_at, '[)') WITH &&"
                ") WHERE (status IN ('pending', 'confirmed'))"
            )
        )
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text("DROP TYPE IF EXISTS user_role"))
        await conn.execute(text("DROP TYPE IF EXISTS schedule_exception_type"))
        await conn.execute(text("DROP TYPE IF EXISTS booking_status"))
        await conn.execute(text("DROP TYPE IF EXISTS booking_source"))
        await conn.execute(text("DROP TYPE IF EXISTS notification_type"))
        await conn.execute(text("DROP TYPE IF EXISTS notification_status"))
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncIterator[AsyncSession]:  # type: ignore[no-untyped-def]
    """Function-scoped session that truncates all tables after each test."""
    sessionmaker = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)
    async with sessionmaker() as session:
        yield session
        await session.rollback()
    async with db_engine.begin() as conn:
        # Truncate everything (including reset enums?). Tables are listed from metadata.
        table_names = ", ".join(f'"{t.name}"' for t in reversed(Base.metadata.sorted_tables))
        if table_names:
            await conn.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE"))


@pytest_asyncio.fixture
async def db_session_factory(db_engine):  # type: ignore[no-untyped-def]
    """Returns a callable that yields new AsyncSession objects bound to the test engine.

    Useful for tests that need to simulate distinct concurrent sessions (e.g. the
    worker creates its own session per tick).
    """
    factory = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)
    return factory


@pytest.fixture
def settings() -> Settings:
    return get_settings()


@pytest_asyncio.fixture
async def client(db_engine, settings) -> AsyncIterator[AsyncClient]:  # type: ignore[no-untyped-def]
    from unittest.mock import AsyncMock

    from aiogram import Bot
    from fastapi import FastAPI

    sessionmaker = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with sessionmaker() as session:
            yield session

    app = FastAPI(title="SlotBook API (test)")
    from app.api.router import api_router
    from app.api.routes import health
    from app.core.errors import install_exception_handlers

    install_exception_handlers(app)
    app.include_router(health.router, tags=["health"])
    app.include_router(api_router)
    app.dependency_overrides[get_session] = override_session
    app.state.bot = AsyncMock(spec=Bot)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def business(db_session: AsyncSession) -> Business:
    biz = Business(name="Test Studio", timezone="UTC")
    db_session.add(biz)
    await db_session.commit()
    await db_session.refresh(biz)
    # Bootstrap a default branch so legacy fixtures that create
    # Service/StaffMember/Booking can rely on a branch existing.
    default_branch = Branch(
        business_id=biz.id, name=biz.name, timezone=biz.timezone, sort_order=0
    )
    db_session.add(default_branch)
    await db_session.commit()
    await db_session.refresh(default_branch)
    # Attach for fixtures/tests that want to reuse it.
    biz._default_branch_id = default_branch.id  # type: ignore[attr-defined]
    return biz


@pytest_asyncio.fixture
async def branch(db_session: AsyncSession, business: Business) -> Branch:
    """Return the default branch created alongside the business fixture."""
    branch_id = getattr(business, "_default_branch_id", None)
    if branch_id is not None:
        existing = await db_session.get(Branch, branch_id)
        if existing is not None:
            return existing
    br = Branch(business_id=business.id, name=business.name, timezone=business.timezone, sort_order=0)
    db_session.add(br)
    await db_session.commit()
    await db_session.refresh(br)
    return br


@pytest_asyncio.fixture
async def client_user(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=1001, first_name="Client", role=UserRole.CLIENT, last_seen_at=datetime.now(UTC)
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=2002, first_name="Admin", role=UserRole.ADMIN, last_seen_at=datetime.now(UTC)
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def superadmin_user(db_session: AsyncSession) -> User:
    user = User(
        telegram_id=3003,
        first_name="SuperAdmin",
        role=UserRole.SUPERADMIN,
        last_seen_at=datetime.now(UTC),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def auth_headers(user: User, settings: Settings) -> dict[str, str]:
    from datetime import timedelta

    token = issue_jwt(
        subject=str(user.id),
        role=user.role.value,
        secret=settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
        expires_in=timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    )
    return {"Authorization": f"Bearer {token}"}
