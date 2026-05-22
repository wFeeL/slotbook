"""Integration test for SELECT FOR UPDATE race protection on concurrent booking creation.

Two concurrent BookingService.create_booking calls compete for the same slot.
Exactly one must succeed; the other must raise SlotAlreadyTaken.
Final row count in bookings must be exactly 1.

Implementation details:
  - Two OS threads are used, each running its own asyncio event loop.
  - Each thread creates its own create_async_engine and asyncpg connection pool,
    so the DB connections are completely independent and truly concurrent.
  - threading.Barrier(2) synchronises both threads at the point just before each
    calls create_booking, maximising the chance of overlapping DB transactions.
  - The test validates two layers of protection:
    1. SELECT FOR UPDATE in BookingService catches conflicts when a row already exists
       and the second transaction blocks then re-checks.
    2. The unique partial index (bookings_active_by_staff on status IN ('pending','confirmed'))
       catches the edge case where both transactions INSERT simultaneously on an empty table
       — the DB rejects the duplicate with an IntegrityError that is translated to SlotAlreadyTaken.
"""

from __future__ import annotations

import asyncio
import threading
from datetime import UTC, datetime, time, timedelta

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.errors import SlotAlreadyTaken
from app.db.enums import BookingSource, UserRole
from app.db.models.booking import Booking
from app.db.models.business import Business
from app.db.models.schedule import WorkingHours
from app.db.models.service import Service
from app.db.models.staff import StaffMember, StaffService
from app.db.models.user import User
from app.services.booking_service import BookingService


def _race_slot() -> datetime:
    """Return a tz-aware datetime 3 days in future at 10:00 UTC."""
    base = datetime.now(UTC).replace(hour=10, minute=0, second=0, microsecond=0)
    return base + timedelta(days=3)


def _resolve_test_db_url() -> str:
    import os

    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        raise RuntimeError("TEST_DATABASE_URL is not set")
    return url


def _run_attempt_in_thread(
    db_url: str,
    biz_id: int,
    staff_id: int,
    svc_id: int,
    client_id: int,
    slot: datetime,
    barrier: threading.Barrier,
) -> Booking | Exception:
    """Run create_booking in its own OS thread with its own event loop and engine."""

    async def _inner() -> Booking:
        engine = create_async_engine(db_url, future=True)
        try:
            maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
            async with maker() as session:
                local_biz = await session.get(Business, biz_id)
                assert local_biz is not None
                # Synchronise: both threads reach this point before either starts its
                # transaction.  This maximises the chance of overlapping transactions.
                barrier.wait()
                return await BookingService(session).create_booking(
                    business=local_biz,
                    actor_user_id=client_id,
                    client_id=client_id,
                    staff_id=staff_id,
                    service_id=svc_id,
                    starts_at=slot,
                    source=BookingSource.MINI_APP,
                )
        finally:
            await engine.dispose()

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_inner())
    except Exception as exc:
        return exc
    finally:
        loop.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_race_condition_only_one_booking_created(db_engine) -> None:  # type: ignore[no-untyped-def]
    """
    Two threads each run create_booking for the same slot simultaneously.
    SELECT FOR UPDATE ensures exactly one wins; the other gets SlotAlreadyTaken.
    Final booking count must be exactly 1.
    """
    # -----------------------------------------------------------------------
    # 1. Seed data in a single session
    # -----------------------------------------------------------------------
    factory = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)

    async with factory() as seed_session:
        # Truncate relevant tables to start clean
        await seed_session.execute(
            text(
                "TRUNCATE notifications, audit_logs, bookings, staff_services, "
                "working_hours, schedule_exceptions, staff_members, "
                "services, businesses, users RESTART IDENTITY CASCADE"
            )
        )
        await seed_session.commit()

        biz = Business(
            name="Race Studio",
            timezone="UTC",
            booking_buffer_minutes=0,
            min_cancellation_hours=2,
            slot_step_minutes=15,
        )
        seed_session.add(biz)
        await seed_session.flush()

        svc = Service(business_id=biz.id, title="Race Cut", duration_minutes=60)
        staff = StaffMember(business_id=biz.id, name="RaceStaff")
        seed_session.add_all([svc, staff])
        await seed_session.flush()

        seed_session.add(StaffService(staff_id=staff.id, service_id=svc.id))

        # 24h working hours for all weekdays
        for d in range(7):
            seed_session.add(
                WorkingHours(
                    staff_id=staff.id,
                    weekday=d,
                    start_time=time(0, 0),
                    end_time=time(23, 59),
                    is_active=True,
                )
            )

        client1 = User(
            telegram_id=100001,
            first_name="Client1",
            role=UserRole.CLIENT,
            last_seen_at=datetime.now(UTC),
        )
        client2 = User(
            telegram_id=100002,
            first_name="Client2",
            role=UserRole.CLIENT,
            last_seen_at=datetime.now(UTC),
        )
        seed_session.add_all([client1, client2])
        await seed_session.commit()

        await seed_session.refresh(biz)
        await seed_session.refresh(svc)
        await seed_session.refresh(staff)
        await seed_session.refresh(client1)
        await seed_session.refresh(client2)

        biz_id = biz.id
        svc_id = svc.id
        staff_id = staff.id
        c1_id = client1.id
        c2_id = client2.id

    slot = _race_slot()
    db_url = _resolve_test_db_url()

    # -----------------------------------------------------------------------
    # 2. Two OS threads, each with its own event loop, compete for the same slot.
    #    A threading.Barrier synchronises both threads so they start their
    #    transactions at the same instant, maximising lock contention.
    # -----------------------------------------------------------------------
    barrier = threading.Barrier(2)

    result1: list[Booking | Exception] = []
    result2: list[Booking | Exception] = []

    def thread1() -> None:
        result1.append(
            _run_attempt_in_thread(db_url, biz_id, staff_id, svc_id, c1_id, slot, barrier)
        )

    def thread2() -> None:
        result2.append(
            _run_attempt_in_thread(db_url, biz_id, staff_id, svc_id, c2_id, slot, barrier)
        )

    t1 = threading.Thread(target=thread1)
    t2 = threading.Thread(target=thread2)
    t1.start()
    t2.start()
    # Run threads in an executor so we don't block the event loop
    await asyncio.get_event_loop().run_in_executor(None, t1.join)
    await asyncio.get_event_loop().run_in_executor(None, t2.join)

    results = [result1[0], result2[0]]

    successes = [r for r in results if isinstance(r, Booking)]
    failures = [r for r in results if isinstance(r, SlotAlreadyTaken)]
    other_errors = [r for r in results if not isinstance(r, (Booking, SlotAlreadyTaken))]

    assert other_errors == [], f"Unexpected errors: {other_errors}"
    assert len(successes) == 1, f"Expected exactly 1 success, got {len(successes)}: {results}"
    assert len(failures) == 1, (
        f"Expected exactly 1 SlotAlreadyTaken, got {len(failures)}: {results}"
    )

    # -----------------------------------------------------------------------
    # 3. Verify exactly 1 booking row in DB
    # -----------------------------------------------------------------------
    async with factory() as verify_session:
        count_result = await verify_session.execute(
            select(func.count()).select_from(Booking).where(Booking.staff_id == staff_id)
        )
        booking_count = count_result.scalar_one()

    assert booking_count == 1, f"Expected exactly 1 booking in DB, found {booking_count}"
