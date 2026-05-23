from __future__ import annotations

from datetime import UTC, datetime, timedelta
from datetime import time as time_t
from unittest.mock import AsyncMock

import pytest
from aiogram import Bot

from app.db.enums import (
    BookingSource,
    BookingStatus,
    NotificationStatus,
    NotificationType,
)
from app.db.models.booking import Booking
from app.db.models.branch import Branch
from app.db.models.business import Business
from app.db.models.notification import Notification
from app.db.models.schedule import WorkingHours
from app.db.models.service import Service
from app.db.models.staff import StaffMember
from app.db.models.user import User
from app.workers.reminders import tick

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


@pytest.fixture
async def world(db_session):
    biz = Business(
        name="Demo",
        timezone="Europe/Moscow",
        admin_chat_id=None,
        slot_step_minutes=15,
        booking_buffer_minutes=0,
        min_cancellation_hours=2,
    )
    db_session.add(biz)
    await db_session.flush()

    branch = Branch(business_id=biz.id, name=biz.name, timezone=biz.timezone, sort_order=0)
    db_session.add(branch)
    await db_session.flush()

    client = User(telegram_id=777, role="client", first_name="Tester")
    db_session.add(client)
    await db_session.flush()

    service = Service(
        business_id=biz.id,
        branch_id=branch.id,
        title="Cut",
        duration_minutes=60,
        is_active=True,
        sort_order=0,
    )
    db_session.add(service)
    await db_session.flush()

    staff = StaffMember(business_id=biz.id, branch_id=branch.id, name="Alex", is_active=True)
    db_session.add(staff)
    await db_session.flush()

    for wd in range(7):
        db_session.add(
            WorkingHours(
                staff_id=staff.id,
                weekday=wd,
                start_time=time_t(9, 0),
                end_time=time_t(21, 0),
                is_active=True,
            )
        )

    starts_at = datetime.now(UTC) + timedelta(hours=1)  # in 1 hour
    starts_at = starts_at.replace(minute=0, second=0, microsecond=0)
    booking = Booking(
        business_id=biz.id,
        branch_id=branch.id,
        client_id=client.id,
        service_id=service.id,
        staff_id=staff.id,
        starts_at=starts_at,
        ends_at=starts_at + timedelta(hours=1),
        status=BookingStatus.CONFIRMED,
        source=BookingSource.MINI_APP,
    )
    db_session.add(booking)
    await db_session.commit()
    return biz, client, service, staff, booking


async def test_tick_sends_due_reminder(db_session_factory, world):
    _biz, client, _service, _staff, booking = world
    # Insert a due reminder (scheduled_at in the past)
    async with db_session_factory() as s:
        n = Notification(
            booking_id=booking.id,
            user_id=client.id,
            notification_type=NotificationType.REMINDER_2H,
            notification_status=NotificationStatus.PENDING,
            scheduled_at=datetime.now(UTC) - timedelta(minutes=5),
        )
        s.add(n)
        await s.commit()
        notif_id = n.id

    bot = AsyncMock(spec=Bot)
    sent = await tick(db_session_factory, bot)
    assert sent >= 1

    async with db_session_factory() as s:
        refreshed = await s.get(Notification, notif_id)
        assert refreshed is not None
        assert refreshed.notification_status == NotificationStatus.SENT
    bot.send_message.assert_called()


async def test_tick_skips_future_reminder(db_session_factory, world):
    _biz, client, _service, _staff, booking = world
    async with db_session_factory() as s:
        n = Notification(
            booking_id=booking.id,
            user_id=client.id,
            notification_type=NotificationType.REMINDER_2H,
            notification_status=NotificationStatus.PENDING,
            scheduled_at=datetime.now(UTC) + timedelta(hours=1),  # future
        )
        s.add(n)
        await s.commit()
        notif_id = n.id

    bot = AsyncMock(spec=Bot)
    await tick(db_session_factory, bot)

    async with db_session_factory() as s:
        refreshed = await s.get(Notification, notif_id)
        assert refreshed.notification_status == NotificationStatus.PENDING
    bot.send_message.assert_not_called()
