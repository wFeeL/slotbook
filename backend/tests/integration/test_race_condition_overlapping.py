"""Two concurrent INSERTs for overlapping bookings on the same staff must
have exactly one success and one 409 -- proves the EXCLUDE constraint."""

from __future__ import annotations

import asyncio
import os
import threading
from datetime import UTC, datetime, time, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.errors import SlotAlreadyTaken
from app.db.enums import BookingSource, UserRole
from app.db.models.booking import Booking
from app.db.models.branch import Branch
from app.db.models.business import Business
from app.db.models.schedule import WorkingHours
from app.db.models.service import Service
from app.db.models.staff import StaffMember, StaffService
from app.db.models.user import User
from app.services.booking_service import BookingService


def _resolve_test_db_url() -> str:
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
    starts_at: datetime,
    barrier: threading.Barrier,
) -> Booking | Exception:
    async def _inner() -> Booking:
        engine = create_async_engine(db_url, future=True)
        try:
            maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
            async with maker() as session:
                local_biz = await session.get(Business, biz_id)
                assert local_biz is not None
                barrier.wait()
                return await BookingService(session).create_booking(
                    business=local_biz,
                    actor_user_id=client_id,
                    client_id=client_id,
                    staff_id=staff_id,
                    service_id=svc_id,
                    starts_at=starts_at,
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
async def test_overlapping_different_starts_one_wins(db_engine) -> None:  # type: ignore[no-untyped-def]
    """Two concurrent INSERTs for *overlapping but distinct* slots on the same
    staff member: 10:00-11:00 vs 10:30-11:30. The partial UNIQUE index doesn't
    catch this because starts_at differs; only the EXCLUDE constraint does.

    Exactly one must succeed; the other must raise SlotAlreadyTaken.
    """
    factory = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)

    async with factory() as seed_session:
        await seed_session.execute(
            text(
                "TRUNCATE notifications, audit_logs, bookings, staff_services, "
                "working_hours, schedule_exceptions, staff_members, "
                "services, branches, businesses, users RESTART IDENTITY CASCADE"
            )
        )
        await seed_session.commit()

        biz = Business(
            name="Overlap Studio",
            timezone="UTC",
            booking_buffer_minutes=0,
            min_cancellation_hours=2,
            slot_step_minutes=15,
        )
        seed_session.add(biz)
        await seed_session.flush()

        branch = Branch(business_id=biz.id, name=biz.name, timezone=biz.timezone, sort_order=0)
        seed_session.add(branch)
        await seed_session.flush()

        svc = Service(business_id=biz.id, branch_id=branch.id, title="Cut", duration_minutes=60)
        staff = StaffMember(business_id=biz.id, branch_id=branch.id, name="Alex")
        seed_session.add_all([svc, staff])
        await seed_session.flush()

        seed_session.add(StaffService(staff_id=staff.id, service_id=svc.id))
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

        c1 = User(
            telegram_id=300001,
            first_name="C1",
            role=UserRole.CLIENT,
            last_seen_at=datetime.now(UTC),
        )
        c2 = User(
            telegram_id=300002,
            first_name="C2",
            role=UserRole.CLIENT,
            last_seen_at=datetime.now(UTC),
        )
        seed_session.add_all([c1, c2])
        await seed_session.commit()

        biz_id = biz.id
        svc_id = svc.id
        staff_id = staff.id
        c1_id = c1.id
        c2_id = c2.id

    base = (datetime.now(UTC) + timedelta(days=2)).replace(
        hour=10, minute=0, second=0, microsecond=0
    )
    starts_a = base
    starts_b = base + timedelta(minutes=30)  # 10:00-11:00 overlaps 10:30-11:30

    db_url = _resolve_test_db_url()
    barrier = threading.Barrier(2)
    res1: list[Booking | Exception] = []
    res2: list[Booking | Exception] = []

    def t1() -> None:
        res1.append(
            _run_attempt_in_thread(db_url, biz_id, staff_id, svc_id, c1_id, starts_a, barrier)
        )

    def t2() -> None:
        res2.append(
            _run_attempt_in_thread(db_url, biz_id, staff_id, svc_id, c2_id, starts_b, barrier)
        )

    th1 = threading.Thread(target=t1)
    th2 = threading.Thread(target=t2)
    th1.start()
    th2.start()
    await asyncio.get_event_loop().run_in_executor(None, th1.join)
    await asyncio.get_event_loop().run_in_executor(None, th2.join)

    results = [res1[0], res2[0]]
    successes = [r for r in results if isinstance(r, Booking)]
    failures = [r for r in results if isinstance(r, SlotAlreadyTaken)]
    other_errors = [r for r in results if not isinstance(r, (Booking, SlotAlreadyTaken))]

    assert other_errors == [], f"Unexpected errors: {other_errors}"
    assert len(successes) == 1, f"Expected exactly 1 success, got {len(successes)}: {results}"
    assert len(failures) == 1, (
        f"Expected exactly 1 SlotAlreadyTaken, got {len(failures)}: {results}"
    )
