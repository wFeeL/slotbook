from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.db.enums import BookingStatus, NotificationType, UserRole
from app.db.models.booking import Booking
from app.db.models.notification import Notification
from app.db.models.service import Service
from app.db.models.staff import StaffMember
from app.db.models.user import User
from tests.conftest import auth_headers


async def _confirmed_booking(db_session, business, client_user) -> Booking:
    svc = Service(
        business_id=business.id, branch_id=business._default_branch_id,
        title="S", duration_minutes=30,
    )
    db_session.add(svc)
    staff = StaffMember(business_id=business.id, branch_id=business._default_branch_id, name="M")
    db_session.add(staff)
    await db_session.flush()
    starts = datetime.now(UTC) - timedelta(hours=2)
    bk = Booking(
        business_id=business.id, branch_id=business._default_branch_id,
        client_id=client_user.id, staff_id=staff.id, service_id=svc.id,
        starts_at=starts, ends_at=starts + timedelta(minutes=30),
        status=BookingStatus.CONFIRMED,
    )
    db_session.add(bk)
    await db_session.commit()
    await db_session.refresh(bk)
    return bk


@pytest.mark.asyncio
async def test_completion_enqueues_review_request_at_t_plus_2h(
    client, db_session, business, client_user, admin_user, settings
) -> None:
    bk = await _confirmed_booking(db_session, business, client_user)
    res = await client.patch(
        f"/api/v1/admin/bookings/{bk.id}",
        json={"status": "completed"},
        headers=auth_headers(admin_user, settings),
    )
    assert res.status_code == 200, res.text

    rows = (await db_session.execute(
        select(Notification).where(
            Notification.notification_type == NotificationType.REVIEW_REQUEST,
            Notification.booking_id == bk.id,
        )
    )).scalars().all()
    assert len(rows) == 1
    n = rows[0]
    assert n.user_id == client_user.id
    delta = (n.scheduled_at - datetime.now(UTC)).total_seconds()
    assert 7000 < delta < 7400


@pytest.mark.asyncio
async def test_duplicate_completion_does_not_double_enqueue(
    client, db_session, business, client_user, admin_user, settings
) -> None:
    bk = await _confirmed_booking(db_session, business, client_user)
    for _ in range(2):
        res = await client.patch(
            f"/api/v1/admin/bookings/{bk.id}",
            json={"status": "completed"},
            headers=auth_headers(admin_user, settings),
        )
        assert res.status_code == 200, res.text
    rows = (await db_session.execute(
        select(Notification).where(
            Notification.notification_type == NotificationType.REVIEW_REQUEST,
            Notification.booking_id == bk.id,
        )
    )).scalars().all()
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_skips_when_user_opted_out_reminders(
    client, db_session, business, admin_user, settings
) -> None:
    user = User(
        telegram_id=9301, first_name="Opt", role=UserRole.CLIENT, reminders_enabled=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    bk = await _confirmed_booking(db_session, business, user)
    res = await client.patch(
        f"/api/v1/admin/bookings/{bk.id}",
        json={"status": "completed"},
        headers=auth_headers(admin_user, settings),
    )
    assert res.status_code == 200
    rows = (await db_session.execute(
        select(Notification).where(
            Notification.notification_type == NotificationType.REVIEW_REQUEST
        )
    )).scalars().all()
    assert rows == []
