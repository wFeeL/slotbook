from __future__ import annotations

from datetime import UTC, datetime, time as time_t, timedelta

import pytest
from sqlalchemy import select

from app.db.enums import (
    NotificationStatus,
    NotificationType,
    UserRole,
)
from app.db.models.notification import Notification
from app.db.models.schedule import WorkingHours
from app.db.models.service import Service
from app.db.models.staff import StaffMember, StaffService
from app.db.models.user import User
from app.services.booking_service import BookingService


async def _setup(db_session, business, *, link_staff_to_user: bool):
    user_staff = User(telegram_id=7777, first_name="Mast", role=UserRole.STAFF)
    user_client = User(telegram_id=7778, first_name="Cli", role=UserRole.CLIENT)
    db_session.add_all([user_staff, user_client])
    await db_session.flush()

    svc = Service(
        business_id=business.id,
        branch_id=business._default_branch_id,
        title="S",
        duration_minutes=30,
    )
    db_session.add(svc)
    await db_session.flush()

    staff = StaffMember(
        business_id=business.id,
        branch_id=business._default_branch_id,
        name="Mast",
        is_active=True,
        user_id=(user_staff.id if link_staff_to_user else None),
    )
    db_session.add(staff)
    await db_session.flush()
    db_session.add(StaffService(staff_id=staff.id, service_id=svc.id))
    for wd in range(7):
        db_session.add(
            WorkingHours(
                staff_id=staff.id,
                weekday=wd,
                start_time=time_t(0, 0),
                end_time=time_t(23, 59),
                is_active=True,
            )
        )
    await db_session.commit()
    return svc, staff, user_client, user_staff


def _aligned_starts(business, *, hours_ahead: int) -> datetime:
    """Pick a slot at top of hour (always aligned to any step) that is in the future."""
    return (
        datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
        + timedelta(hours=hours_ahead + 1)
    )


@pytest.mark.asyncio
async def test_create_booking_enqueues_staff_notification_when_linked(
    db_session, business
) -> None:
    svc, staff, client_u, staff_u = await _setup(
        db_session, business, link_staff_to_user=True
    )
    starts = _aligned_starts(business, hours_ahead=2)

    await BookingService(db_session).create_booking(
        business=business,
        actor_user_id=client_u.id,
        client_id=client_u.id,
        staff_id=staff.id,
        service_id=svc.id,
        starts_at=starts,
    )

    notifs = (
        await db_session.execute(
            select(Notification).where(
                Notification.notification_type == NotificationType.BOOKING_CREATED_STAFF,
                Notification.user_id == staff_u.id,
            )
        )
    ).scalars().all()
    assert len(list(notifs)) == 1
    assert notifs[0].notification_status == NotificationStatus.PENDING


@pytest.mark.asyncio
async def test_create_booking_skips_staff_notification_when_unlinked(
    db_session, business
) -> None:
    svc, staff, client_u, _ = await _setup(
        db_session, business, link_staff_to_user=False
    )
    starts = _aligned_starts(business, hours_ahead=2)

    await BookingService(db_session).create_booking(
        business=business,
        actor_user_id=client_u.id,
        client_id=client_u.id,
        staff_id=staff.id,
        service_id=svc.id,
        starts_at=starts,
    )

    rows = (
        await db_session.execute(
            select(Notification).where(
                Notification.notification_type == NotificationType.BOOKING_CREATED_STAFF
            )
        )
    ).scalars().all()
    assert list(rows) == []


@pytest.mark.asyncio
async def test_create_booking_skips_staff_when_staff_user_is_client(
    db_session, business
) -> None:
    user = User(telegram_id=7779, first_name="Both", role=UserRole.STAFF)
    db_session.add(user)
    await db_session.flush()
    svc = Service(
        business_id=business.id,
        branch_id=business._default_branch_id,
        title="S",
        duration_minutes=30,
    )
    db_session.add(svc)
    await db_session.flush()
    staff = StaffMember(
        business_id=business.id,
        branch_id=business._default_branch_id,
        name="Both",
        user_id=user.id,
        is_active=True,
    )
    db_session.add(staff)
    await db_session.flush()
    db_session.add(StaffService(staff_id=staff.id, service_id=svc.id))
    for wd in range(7):
        db_session.add(
            WorkingHours(
                staff_id=staff.id, weekday=wd,
                start_time=time_t(0, 0), end_time=time_t(23, 59),
                is_active=True,
            )
        )
    await db_session.commit()
    starts = _aligned_starts(business, hours_ahead=2)

    await BookingService(db_session).create_booking(
        business=business,
        actor_user_id=user.id,
        client_id=user.id,
        staff_id=staff.id,
        service_id=svc.id,
        starts_at=starts,
    )

    rows = (
        await db_session.execute(
            select(Notification).where(
                Notification.notification_type == NotificationType.BOOKING_CREATED_STAFF
            )
        )
    ).scalars().all()
    assert list(rows) == []


@pytest.mark.asyncio
async def test_cancel_booking_enqueues_staff_notification(
    db_session, business
) -> None:
    svc, staff, client_u, staff_u = await _setup(
        db_session, business, link_staff_to_user=True
    )
    starts = _aligned_starts(business, hours_ahead=24)
    booking = await BookingService(db_session).create_booking(
        business=business,
        actor_user_id=client_u.id,
        client_id=client_u.id,
        staff_id=staff.id,
        service_id=svc.id,
        starts_at=starts,
    )

    await BookingService(db_session).cancel_booking(
        business=business,
        actor_user_id=client_u.id,
        actor_role=UserRole.CLIENT,
        booking_id=booking.id,
    )

    notifs = (
        await db_session.execute(
            select(Notification).where(
                Notification.notification_type == NotificationType.BOOKING_CANCELLED_STAFF,
                Notification.user_id == staff_u.id,
            )
        )
    ).scalars().all()
    assert len(list(notifs)) == 1


@pytest.mark.asyncio
async def test_reschedule_booking_enqueues_staff_notification(
    db_session, business
) -> None:
    svc, staff, client_u, staff_u = await _setup(
        db_session, business, link_staff_to_user=True
    )
    starts = _aligned_starts(business, hours_ahead=24)
    booking = await BookingService(db_session).create_booking(
        business=business,
        actor_user_id=client_u.id,
        client_id=client_u.id,
        staff_id=staff.id,
        service_id=svc.id,
        starts_at=starts,
    )

    new_starts = starts + timedelta(hours=1)
    await BookingService(db_session).reschedule_booking(
        business=business,
        actor_user_id=client_u.id,
        actor_role=UserRole.CLIENT,
        booking_id=booking.id,
        new_starts_at=new_starts,
    )

    notifs = (
        await db_session.execute(
            select(Notification).where(
                Notification.notification_type == NotificationType.BOOKING_RESCHEDULED_STAFF,
                Notification.user_id == staff_u.id,
            )
        )
    ).scalars().all()
    assert len(list(notifs)) == 1
