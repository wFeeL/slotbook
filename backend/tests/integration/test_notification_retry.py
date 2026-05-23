from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from app.db.enums import (
    BookingSource,
    BookingStatus,
    NotificationStatus,
    NotificationType,
)
from app.db.models.booking import Booking
from app.db.models.business import Business
from app.db.models.notification import Notification
from app.db.models.service import Service
from app.db.models.staff import StaffMember
from app.db.models.user import User
from app.services.notification_retry import MAX_RETRIES
from app.services.notification_service import NotificationService

pytestmark = [pytest.mark.asyncio]


@pytest.fixture
async def world(db_session):
    biz = Business(
        name="Demo",
        timezone="Europe/Moscow",
        slot_step_minutes=15,
        booking_buffer_minutes=0,
        min_cancellation_hours=2,
    )
    db_session.add(biz)
    await db_session.flush()
    client = User(telegram_id=200, role="client", first_name="C")
    db_session.add(client)
    await db_session.flush()
    service = Service(
        business_id=biz.id, title="Cut", duration_minutes=60, is_active=True, sort_order=0
    )
    db_session.add(service)
    await db_session.flush()
    staff = StaffMember(business_id=biz.id, name="Alex", is_active=True)
    db_session.add(staff)
    await db_session.flush()
    starts_at = datetime.now(UTC) + timedelta(hours=1)
    starts_at = starts_at.replace(minute=0, second=0, microsecond=0)
    booking = Booking(
        business_id=biz.id,
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


async def test_first_failure_increments_retry_count(db_session, world):
    biz, client, service, staff, booking = world
    n = Notification(
        booking_id=booking.id,
        user_id=client.id,
        notification_type=NotificationType.BOOKING_CREATED_CLIENT,
        notification_status=NotificationStatus.PENDING,
    )
    db_session.add(n)
    await db_session.commit()

    bot = AsyncMock(spec=Bot)
    bot.send_message.side_effect = TelegramAPIError(method="x", message="boom")
    await NotificationService(db_session, bot).dispatch_pending_for_booking(booking.id)

    await db_session.refresh(n)
    assert n.notification_status == NotificationStatus.PENDING
    assert n.retry_count == 1
    assert n.next_retry_at is not None


async def test_max_retries_marks_failed(db_session, world):
    biz, client, service, staff, booking = world
    n = Notification(
        booking_id=booking.id,
        user_id=client.id,
        notification_type=NotificationType.BOOKING_CREATED_CLIENT,
        notification_status=NotificationStatus.PENDING,
        retry_count=MAX_RETRIES - 1,
    )
    db_session.add(n)
    await db_session.commit()

    bot = AsyncMock(spec=Bot)
    bot.send_message.side_effect = TelegramAPIError(method="x", message="boom")
    await NotificationService(db_session, bot).dispatch_pending_for_booking(booking.id)

    await db_session.refresh(n)
    assert n.notification_status == NotificationStatus.FAILED
    assert n.error_message is not None
