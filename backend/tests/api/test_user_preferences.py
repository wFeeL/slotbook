from __future__ import annotations

from datetime import UTC, datetime, time as time_t, timedelta

import pytest
from sqlalchemy import select

from app.db.enums import NotificationType, UserRole
from app.db.models.notification import Notification
from app.db.models.schedule import WorkingHours
from app.db.models.service import Service
from app.db.models.staff import StaffMember, StaffService
from app.db.models.user import User
from app.services.booking_service import BookingService
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_get_me_returns_reminder_pref(client, client_user, settings) -> None:
    res = await client.get("/api/v1/users/me", headers=auth_headers(client_user, settings))
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["reminders_enabled"] is True


@pytest.mark.asyncio
async def test_patch_me_preferences_toggles_reminders(
    client, db_session, client_user, settings
) -> None:
    res = await client.patch(
        "/api/v1/users/me/preferences",
        json={"reminders_enabled": False},
        headers=auth_headers(client_user, settings),
    )
    assert res.status_code == 200, res.text
    assert res.json()["reminders_enabled"] is False

    await db_session.refresh(client_user)
    assert client_user.reminders_enabled is False


@pytest.mark.asyncio
async def test_create_booking_skips_reminders_when_user_opted_out(
    db_session, business
) -> None:
    user = User(telegram_id=8001, first_name="O", role=UserRole.CLIENT, reminders_enabled=False)
    db_session.add(user)
    await db_session.flush()
    svc = Service(
        business_id=business.id, branch_id=business._default_branch_id,
        title="S", duration_minutes=30,
    )
    db_session.add(svc)
    await db_session.flush()
    staff = StaffMember(
        business_id=business.id, branch_id=business._default_branch_id, name="M",
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

    starts = datetime.now(UTC).replace(minute=0, second=0, microsecond=0) + timedelta(hours=25)
    await BookingService(db_session).create_booking(
        business=business, actor_user_id=user.id, client_id=user.id,
        staff_id=staff.id, service_id=svc.id, starts_at=starts,
    )

    rows = (
        await db_session.execute(
            select(Notification).where(
                Notification.notification_type.in_(
                    [NotificationType.REMINDER_24H, NotificationType.REMINDER_2H]
                )
            )
        )
    ).scalars().all()
    assert list(rows) == []
