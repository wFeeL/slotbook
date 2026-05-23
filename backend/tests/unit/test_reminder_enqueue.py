from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.db.enums import (
    BookingSource,
    NotificationStatus,
    NotificationType,
)
from app.db.models.branch import Branch
from app.db.models.business import Business
from app.db.models.notification import Notification
from app.db.models.schedule import WorkingHours
from app.db.models.service import Service
from app.db.models.staff import StaffMember
from app.db.models.user import User
from app.services.booking_service import BookingService

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def seed(db_session):
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

    client = User(telegram_id=10, role="client", first_name="Cli")
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

    # Link service to staff
    from app.db.repositories.staff import StaffRepo

    await StaffRepo(db_session).replace_services(staff.id, [service.id])

    # Add working hours for all days 09:00-21:00
    from datetime import time as time_t

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
    await db_session.commit()
    return biz, client, service, staff


async def test_create_booking_enqueues_two_reminders(db_session, seed):
    biz, client, service, staff = seed
    starts_at = datetime.now(UTC) + timedelta(days=3)
    starts_at = starts_at.replace(minute=0, second=0, microsecond=0)
    booking = await BookingService(db_session).create_booking(
        business=biz,
        actor_user_id=client.id,
        client_id=client.id,
        staff_id=staff.id,
        service_id=service.id,
        starts_at=starts_at,
        source=BookingSource.MINI_APP,
    )

    rows = (
        await db_session.execute(
            select(Notification).where(Notification.booking_id == booking.id)
        )
    ).scalars().all()

    by_type = {r.notification_type: r for r in rows}
    assert NotificationType.REMINDER_24H in by_type
    assert NotificationType.REMINDER_2H in by_type
    r24 = by_type[NotificationType.REMINDER_24H]
    r2 = by_type[NotificationType.REMINDER_2H]

    # scheduled_at should equal starts_at - 24h / -2h
    assert r24.scheduled_at is not None
    assert r2.scheduled_at is not None
    assert abs((r24.scheduled_at - (starts_at - timedelta(hours=24))).total_seconds()) < 2
    assert abs((r2.scheduled_at - (starts_at - timedelta(hours=2))).total_seconds()) < 2
    assert r24.notification_status == NotificationStatus.PENDING
    assert r2.notification_status == NotificationStatus.PENDING


async def test_cancel_booking_deletes_pending_reminders(db_session, seed):
    biz, client, service, staff = seed
    starts_at = datetime.now(UTC) + timedelta(days=3)
    starts_at = starts_at.replace(minute=0, second=0, microsecond=0)
    booking = await BookingService(db_session).create_booking(
        business=biz,
        actor_user_id=client.id,
        client_id=client.id,
        staff_id=staff.id,
        service_id=service.id,
        starts_at=starts_at,
        source=BookingSource.MINI_APP,
    )

    # Confirm reminders exist
    pre = (
        await db_session.execute(
            select(Notification).where(
                Notification.booking_id == booking.id,
                Notification.notification_type.in_(
                    (NotificationType.REMINDER_24H, NotificationType.REMINDER_2H)
                ),
            )
        )
    ).scalars().all()
    assert len(pre) == 2

    # Cancel as admin (so client time-limit check doesn't fire)
    from app.db.enums import UserRole
    admin = User(telegram_id=20, role=UserRole.ADMIN, first_name="Adm")
    db_session.add(admin)
    await db_session.commit()

    await BookingService(db_session).cancel_booking(
        business=biz,
        actor_user_id=admin.id,
        actor_role=UserRole.ADMIN,
        booking_id=booking.id,
    )

    post = (
        await db_session.execute(
            select(Notification).where(
                Notification.booking_id == booking.id,
                Notification.notification_type.in_(
                    (NotificationType.REMINDER_24H, NotificationType.REMINDER_2H)
                ),
            )
        )
    ).scalars().all()
    assert post == []
