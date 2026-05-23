"""Integration tests for booking reschedule (client + admin)."""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta

import pytest
from sqlalchemy import select

from app.db.enums import BookingStatus, NotificationType
from app.db.models.notification import Notification
from tests.conftest import auth_headers


def _future_slot(days: int = 2, hour: int = 12) -> datetime:
    base = datetime.now(UTC).replace(hour=hour, minute=0, second=0, microsecond=0)
    return base + timedelta(days=days)


async def _seed(db_session, business):  # type: ignore[no-untyped-def]
    """Create service + staff + StaffService + 24h working hours."""
    from app.db.models.schedule import WorkingHours
    from app.db.models.service import Service
    from app.db.models.staff import StaffMember, StaffService

    svc = Service(business_id=business.id, title="Haircut", duration_minutes=60)
    staff = StaffMember(business_id=business.id, name="Bob")
    db_session.add_all([svc, staff])
    await db_session.flush()
    db_session.add(StaffService(staff_id=staff.id, service_id=svc.id))
    for d in range(7):
        db_session.add(
            WorkingHours(
                staff_id=staff.id,
                weekday=d,
                start_time=time(0, 0),
                end_time=time(23, 59),
                is_active=True,
            )
        )
    await db_session.commit()
    return svc, staff


async def _create_booking_via_api(
    client, settings, client_user, svc, staff, starts_at: datetime
) -> int:
    resp = await client.post(
        "/api/v1/bookings",
        json={
            "service_id": svc.id,
            "staff_id": staff.id,
            "starts_at": starts_at.isoformat(),
        },
        headers=auth_headers(client_user, settings),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_client_reschedule_happy_path(
    client, db_session, business, client_user, settings
) -> None:  # type: ignore[no-untyped-def]
    svc, staff = await _seed(db_session, business)
    old_starts_at = _future_slot(days=3, hour=10)
    booking_id = await _create_booking_via_api(
        client, settings, client_user, svc, staff, old_starts_at
    )

    new_starts_at = _future_slot(days=4, hour=14)
    resp = await client.post(
        f"/api/v1/bookings/{booking_id}/reschedule",
        json={"starts_at": new_starts_at.isoformat()},
        headers=auth_headers(client_user, settings),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == booking_id
    # Compare normalised ISO strings — the server returns UTC.
    returned = datetime.fromisoformat(body["starts_at"])
    assert returned.astimezone(UTC) == new_starts_at

    # Verify reminders & reschedule notification rows.
    rows = (
        await db_session.execute(
            select(Notification).where(Notification.booking_id == booking_id)
        )
    ).scalars().all()
    types = [r.notification_type for r in rows]
    # Pending reminders are aligned to the new starts_at.
    reminder_24h_rows = [
        r for r in rows if r.notification_type == NotificationType.REMINDER_24H
    ]
    reminder_2h_rows = [
        r for r in rows if r.notification_type == NotificationType.REMINDER_2H
    ]
    assert len(reminder_24h_rows) == 1
    assert len(reminder_2h_rows) == 1
    assert abs(
        (reminder_24h_rows[0].scheduled_at - (new_starts_at - timedelta(hours=24))).total_seconds()
    ) < 2
    assert abs(
        (reminder_2h_rows[0].scheduled_at - (new_starts_at - timedelta(hours=2))).total_seconds()
    ) < 2
    assert NotificationType.BOOKING_RESCHEDULED_CLIENT in types


@pytest.mark.asyncio
async def test_admin_reschedule_happy_path(
    client, db_session, business, client_user, admin_user, settings
) -> None:  # type: ignore[no-untyped-def]
    svc, staff = await _seed(db_session, business)
    old_starts_at = _future_slot(days=3, hour=10)
    booking_id = await _create_booking_via_api(
        client, settings, client_user, svc, staff, old_starts_at
    )

    new_starts_at = _future_slot(days=5, hour=11)
    resp = await client.post(
        f"/api/v1/admin/bookings/{booking_id}/reschedule",
        json={"starts_at": new_starts_at.isoformat()},
        headers=auth_headers(admin_user, settings),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == booking_id
    returned = datetime.fromisoformat(body["starts_at"])
    assert returned.astimezone(UTC) == new_starts_at


@pytest.mark.asyncio
async def test_reschedule_taken_slot_returns_409(
    client, db_session, business, client_user, settings
) -> None:  # type: ignore[no-untyped-def]
    svc, staff = await _seed(db_session, business)

    # Two distinct bookings at different times.
    slot_a = _future_slot(days=3, hour=10)
    slot_b = _future_slot(days=3, hour=12)
    booking_a_id = await _create_booking_via_api(
        client, settings, client_user, svc, staff, slot_a
    )
    await _create_booking_via_api(client, settings, client_user, svc, staff, slot_b)

    # Try to reschedule booking_a INTO booking_b's slot.
    resp = await client.post(
        f"/api/v1/bookings/{booking_a_id}/reschedule",
        json={"starts_at": slot_b.isoformat()},
        headers=auth_headers(client_user, settings),
    )
    assert resp.status_code == 409, resp.text
    assert resp.json()["detail"]["code"] == "slot_already_taken"


@pytest.mark.asyncio
async def test_reschedule_cancelled_booking_returns_422(
    client, db_session, business, client_user, admin_user, settings
) -> None:  # type: ignore[no-untyped-def]
    svc, staff = await _seed(db_session, business)

    slot = _future_slot(days=3, hour=10)
    booking_id = await _create_booking_via_api(
        client, settings, client_user, svc, staff, slot
    )

    # Cancel via admin so the min_cancellation window does not matter.
    cancel_resp = await client.post(
        f"/api/v1/admin/bookings/{booking_id}/cancel",
        headers=auth_headers(admin_user, settings),
    )
    assert cancel_resp.status_code == 200, cancel_resp.text
    assert cancel_resp.json()["status"] == BookingStatus.CANCELLED_BY_ADMIN.value

    new_starts_at = _future_slot(days=5, hour=11)
    resp = await client.post(
        f"/api/v1/bookings/{booking_id}/reschedule",
        json={"starts_at": new_starts_at.isoformat()},
        headers=auth_headers(client_user, settings),
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["detail"]["code"] == "cannot_cancel_in_current_status"


@pytest.mark.asyncio
async def test_client_reschedule_too_late_returns_422(
    client, db_session, business, client_user, settings
) -> None:  # type: ignore[no-untyped-def]
    svc, staff = await _seed(db_session, business)

    # Make the cancellation window very wide so any future slot is "too late".
    business.min_cancellation_hours = 9999
    db_session.add(business)
    await db_session.commit()

    slot = _future_slot(days=3, hour=10)
    booking_id = await _create_booking_via_api(
        client, settings, client_user, svc, staff, slot
    )

    new_starts_at = _future_slot(days=5, hour=11)
    resp = await client.post(
        f"/api/v1/bookings/{booking_id}/reschedule",
        json={"starts_at": new_starts_at.isoformat()},
        headers=auth_headers(client_user, settings),
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["detail"]["code"] == "cancellation_too_late"
