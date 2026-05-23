from datetime import UTC, datetime, time, timedelta
from unittest.mock import AsyncMock

import pytest
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import SendMessage
from sqlalchemy import select

from app.db.enums import (
    BookingSource,
    BookingStatus,
    NotificationStatus,
    NotificationType,
)
from app.db.models.booking import Booking
from app.db.models.notification import Notification
from app.db.models.schedule import WorkingHours
from app.db.models.service import Service
from app.db.models.staff import StaffMember, StaffService
from app.services.notification_service import NotificationService


@pytest.fixture
async def seed_booking_and_notifications(db_session, business, client_user, admin_user):
    svc = Service(business_id=business.id, title="Cut", duration_minutes=60)
    staff = StaffMember(business_id=business.id, name="Eve")
    db_session.add_all([svc, staff])
    await db_session.flush()
    db_session.add(StaffService(staff_id=staff.id, service_id=svc.id))
    for d in range(7):
        db_session.add(
            WorkingHours(
                staff_id=staff.id,
                weekday=d,
                start_time=time(0, 0),
                end_time=time(23, 0),
                is_active=True,
            )
        )
    start = (datetime.now(UTC) + timedelta(days=2)).replace(minute=0, second=0, microsecond=0)
    b = Booking(
        business_id=business.id,
        client_id=client_user.id,
        staff_id=staff.id,
        service_id=svc.id,
        starts_at=start,
        ends_at=start + timedelta(hours=1),
        status=BookingStatus.CONFIRMED,
        source=BookingSource.MINI_APP,
    )
    db_session.add(b)
    await db_session.flush()
    db_session.add_all(
        [
            Notification(
                booking_id=b.id,
                user_id=client_user.id,
                notification_type=NotificationType.BOOKING_CREATED_CLIENT,
                notification_status=NotificationStatus.PENDING,
            ),
            Notification(
                booking_id=b.id,
                user_id=admin_user.id,
                notification_type=NotificationType.BOOKING_CREATED_ADMIN,
                notification_status=NotificationStatus.PENDING,
            ),
        ]
    )
    await db_session.commit()
    return b


async def test_dispatch_marks_sent_on_success(db_session, seed_booking_and_notifications):
    booking_id = seed_booking_and_notifications.id
    bot = AsyncMock(spec=Bot)
    await NotificationService(db_session, bot).dispatch_pending_for_booking(booking_id)

    db_session.sync_session.expire_all()
    rows = (
        (
            await db_session.execute(
                select(Notification).where(Notification.booking_id == booking_id)
            )
        )
        .scalars()
        .all()
    )
    assert {r.notification_status for r in rows} == {NotificationStatus.SENT}
    assert all(r.sent_at is not None for r in rows)


async def test_dispatch_marks_failed_on_telegram_error(db_session, seed_booking_and_notifications):
    booking_id = seed_booking_and_notifications.id
    # Bump retry_count to MAX_RETRIES - 1 so this attempt is the terminal one.
    from app.services.notification_retry import MAX_RETRIES

    rows_pre = (
        (
            await db_session.execute(
                select(Notification).where(Notification.booking_id == booking_id)
            )
        )
        .scalars()
        .all()
    )
    for r in rows_pre:
        r.retry_count = MAX_RETRIES - 1
    await db_session.commit()

    bot = AsyncMock(spec=Bot)
    # Construct a TelegramBadRequest with method=SendMessage(chat_id=1, text="x") to satisfy its constructor.
    err = TelegramBadRequest(method=SendMessage(chat_id=1, text="x"), message="bot blocked")
    bot.send_message.side_effect = err

    await NotificationService(db_session, bot).dispatch_pending_for_booking(booking_id)

    db_session.sync_session.expire_all()
    rows = (
        (
            await db_session.execute(
                select(Notification).where(Notification.booking_id == booking_id)
            )
        )
        .scalars()
        .all()
    )
    assert {r.notification_status for r in rows} == {NotificationStatus.FAILED}
    assert all(r.error_message for r in rows)


async def test_dispatch_no_op_when_no_pending(db_session, seed_booking_and_notifications):
    booking_id = seed_booking_and_notifications.id
    bot = AsyncMock(spec=Bot)
    rows = (
        (
            await db_session.execute(
                select(Notification).where(Notification.booking_id == booking_id)
            )
        )
        .scalars()
        .all()
    )
    for r in rows:
        r.notification_status = NotificationStatus.SENT
    await db_session.commit()

    await NotificationService(db_session, bot).dispatch_pending_for_booking(booking_id)
    bot.send_message.assert_not_called()
