from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from aiogram import Bot

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
from app.services.notification_service import NotificationService

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


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

    branch = Branch(business_id=biz.id, name=biz.name, timezone=biz.timezone, sort_order=0)
    db_session.add(branch)
    await db_session.flush()

    client = User(telegram_id=88, role="client", first_name="C")
    db_session.add(client)
    await db_session.flush()

    service = Service(
        business_id=biz.id, branch_id=branch.id, title="Cut", duration_minutes=60, is_active=True, sort_order=0
    )
    db_session.add(service)
    await db_session.flush()

    staff = StaffMember(business_id=biz.id, branch_id=branch.id, name="Alex", is_active=True)
    db_session.add(staff)
    await db_session.flush()

    from app.db.repositories.staff import StaffRepo

    await StaffRepo(db_session).replace_services(staff.id, [service.id])

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


async def test_immediate_dispatch_does_not_fire_reminders(db_session, world):
    biz, client, service, staff = world
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

    bot = AsyncMock(spec=Bot)
    await NotificationService(db_session, bot).dispatch_pending_for_booking(booking.id)

    # The two reminders must remain PENDING because they have scheduled_at in the future.
    from sqlalchemy import select

    reminders = (
        (
            await db_session.execute(
                select(Notification).where(
                    Notification.booking_id == booking.id,
                    Notification.notification_type.in_(
                        (NotificationType.REMINDER_24H, NotificationType.REMINDER_2H)
                    ),
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(reminders) == 2
    for r in reminders:
        assert r.notification_status == NotificationStatus.PENDING
