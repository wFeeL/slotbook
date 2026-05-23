from __future__ import annotations

from datetime import UTC, datetime, time as dtime, timedelta

import pytest

from app.db.enums import BookingStatus, UserRole
from app.db.models.booking import Booking
from app.db.models.schedule import WorkingHours
from app.db.models.service import Service
from app.db.models.staff import StaffMember
from app.db.models.user import User
from tests.conftest import auth_headers


# ---------------------------------------------------------------------------
# GET /staff/me
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_me_unlinked_returns_linked_false(
    client, business, staff_user, settings
) -> None:
    res = await client.get(
        "/api/v1/staff/me", headers=auth_headers(staff_user, settings)
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["linked"] is False
    assert body["staff"] is None
    assert body["branch"] is None
    assert body["business_timezone"] == business.timezone


@pytest.mark.asyncio
async def test_me_linked_returns_staff(
    client, business, staff_user, linked_staff, settings
) -> None:
    res = await client.get(
        "/api/v1/staff/me", headers=auth_headers(staff_user, settings)
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["linked"] is True
    assert body["staff"]["id"] == linked_staff.id
    assert body["staff"]["name"] == "Master"
    assert body["branch"] is not None
    assert body["branch"]["id"] == linked_staff.branch_id
    assert body["business_timezone"] == business.timezone


@pytest.mark.asyncio
async def test_me_requires_auth(client) -> None:
    res = await client.get("/api/v1/staff/me")
    assert res.status_code == 401


# ---------------------------------------------------------------------------
# GET /staff/me/bookings
# ---------------------------------------------------------------------------


async def _seed_booking(
    db_session,
    business,
    staff: StaffMember,
    *,
    hours_offset: int = 1,
    booking_status: BookingStatus = BookingStatus.CONFIRMED,
) -> Booking:
    svc = Service(
        business_id=business.id,
        branch_id=business._default_branch_id,
        title="Cut",
        duration_minutes=30,
        price="1000",
    )
    db_session.add(svc)
    client_u = User(
        telegram_id=10000 + hours_offset, first_name="Cli", role=UserRole.CLIENT
    )
    db_session.add(client_u)
    await db_session.flush()
    starts = datetime.now(UTC) + timedelta(hours=hours_offset)
    bk = Booking(
        business_id=business.id,
        branch_id=business._default_branch_id,
        client_id=client_u.id,
        service_id=svc.id,
        staff_id=staff.id,
        starts_at=starts,
        ends_at=starts + timedelta(minutes=30),
        status=booking_status,
    )
    db_session.add(bk)
    await db_session.commit()
    await db_session.refresh(bk)
    return bk


@pytest.mark.asyncio
async def test_list_bookings_returns_only_own(
    client, db_session, business, staff_user, linked_staff, settings
) -> None:
    own = await _seed_booking(db_session, business, linked_staff, hours_offset=1)
    other_staff = StaffMember(
        business_id=business.id, branch_id=business._default_branch_id, name="Other"
    )
    db_session.add(other_staff)
    await db_session.commit()
    await db_session.refresh(other_staff)
    foreign = await _seed_booking(db_session, business, other_staff, hours_offset=2)

    res = await client.get(
        "/api/v1/staff/me/bookings", headers=auth_headers(staff_user, settings)
    )
    assert res.status_code == 200, res.text
    ids = [r["id"] for r in res.json()]
    assert own.id in ids
    assert foreign.id not in ids


@pytest.mark.asyncio
async def test_list_bookings_unlinked_user_403(client, staff_user, settings) -> None:
    res = await client.get(
        "/api/v1/staff/me/bookings", headers=auth_headers(staff_user, settings)
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_list_bookings_status_filter(
    client, db_session, business, staff_user, linked_staff, settings
) -> None:
    await _seed_booking(
        db_session, business, linked_staff, hours_offset=1,
        booking_status=BookingStatus.CONFIRMED,
    )
    await _seed_booking(
        db_session, business, linked_staff, hours_offset=2,
        booking_status=BookingStatus.COMPLETED,
    )
    res = await client.get(
        "/api/v1/staff/me/bookings?status=completed",
        headers=auth_headers(staff_user, settings),
    )
    assert res.status_code == 200
    items = res.json()
    assert items
    assert all(item["status"] == "completed" for item in items)


# ---------------------------------------------------------------------------
# PATCH /staff/me/bookings/:id
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patch_booking_completed_changes_status(
    client, db_session, business, staff_user, linked_staff, settings
) -> None:
    bk = await _seed_booking(db_session, business, linked_staff, hours_offset=1)
    res = await client.patch(
        f"/api/v1/staff/me/bookings/{bk.id}",
        json={"status": "completed"},
        headers=auth_headers(staff_user, settings),
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_patch_booking_no_show_changes_status(
    client, db_session, business, staff_user, linked_staff, settings
) -> None:
    bk = await _seed_booking(db_session, business, linked_staff, hours_offset=1)
    res = await client.patch(
        f"/api/v1/staff/me/bookings/{bk.id}",
        json={"status": "no_show"},
        headers=auth_headers(staff_user, settings),
    )
    assert res.status_code == 200
    assert res.json()["status"] == "no_show"


@pytest.mark.asyncio
async def test_patch_booking_cancellation_rejected(
    client, db_session, business, staff_user, linked_staff, settings
) -> None:
    bk = await _seed_booking(db_session, business, linked_staff, hours_offset=1)
    res = await client.patch(
        f"/api/v1/staff/me/bookings/{bk.id}",
        json={"status": "cancelled_by_admin"},
        headers=auth_headers(staff_user, settings),
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_patch_other_staff_booking_404(
    client, db_session, business, staff_user, linked_staff, settings
) -> None:
    other = StaffMember(
        business_id=business.id, branch_id=business._default_branch_id, name="Other"
    )
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)
    foreign = await _seed_booking(db_session, business, other, hours_offset=1)
    res = await client.patch(
        f"/api/v1/staff/me/bookings/{foreign.id}",
        json={"status": "completed"},
        headers=auth_headers(staff_user, settings),
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_patch_booking_admin_comment_only(
    client, db_session, business, staff_user, linked_staff, settings
) -> None:
    bk = await _seed_booking(db_session, business, linked_staff, hours_offset=1)
    res = await client.patch(
        f"/api/v1/staff/me/bookings/{bk.id}",
        json={"admin_comment": "Клиент опоздал на 5 мин"},
        headers=auth_headers(staff_user, settings),
    )
    assert res.status_code == 200
    assert res.json()["admin_comment"] == "Клиент опоздал на 5 мин"


# ---------------------------------------------------------------------------
# GET /staff/me/schedule
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_schedule_returns_seven_days(
    client, db_session, business, staff_user, linked_staff, settings
) -> None:
    wh = WorkingHours(
        staff_id=linked_staff.id,
        weekday=0,
        start_time=dtime(9, 0),
        end_time=dtime(18, 0),
        is_active=True,
    )
    db_session.add(wh)
    await db_session.commit()

    res = await client.get(
        "/api/v1/staff/me/schedule",
        headers=auth_headers(staff_user, settings),
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert len(body["days"]) == 7
    assert "week_start" in body
    assert body["business_timezone"] == business.timezone
    monday = next(d for d in body["days"] if d["weekday"] == 0)
    assert monday["working_intervals"] == [
        {"start_time": "09:00:00", "end_time": "18:00:00"}
    ]


@pytest.mark.asyncio
async def test_schedule_unlinked_403(client, staff_user, settings) -> None:
    res = await client.get(
        "/api/v1/staff/me/schedule",
        headers=auth_headers(staff_user, settings),
    )
    assert res.status_code == 403


# ---------------------------------------------------------------------------
# PUT /staff/me/working-hours, POST/DELETE /staff/me/exceptions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_my_working_hours_empty(
    client, staff_user, linked_staff, settings
) -> None:
    res = await client.get(
        "/api/v1/staff/me/working-hours",
        headers=auth_headers(staff_user, settings),
    )
    assert res.status_code == 200
    assert res.json() == []


@pytest.mark.asyncio
async def test_put_my_working_hours_replaces(
    client, db_session, staff_user, linked_staff, settings
) -> None:
    body = {
        "entries": [
            {
                "weekday": 0,
                "start_time": "09:00:00",
                "end_time": "18:00:00",
                "is_active": True,
            },
            {
                "weekday": 1,
                "start_time": "10:00:00",
                "end_time": "20:00:00",
                "is_active": True,
            },
        ]
    }
    res = await client.put(
        "/api/v1/staff/me/working-hours",
        json=body,
        headers=auth_headers(staff_user, settings),
    )
    assert res.status_code == 204, res.text

    get = await client.get(
        "/api/v1/staff/me/working-hours",
        headers=auth_headers(staff_user, settings),
    )
    rows = get.json()
    assert len(rows) == 2
    assert {r["weekday"] for r in rows} == {0, 1}


@pytest.mark.asyncio
async def test_create_my_exception_day_off(
    client, staff_user, linked_staff, settings
) -> None:
    res = await client.post(
        "/api/v1/staff/me/exceptions",
        json={"date": "2026-06-15", "type": "day_off", "reason": "Отпуск"},
        headers=auth_headers(staff_user, settings),
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["type"] == "day_off"
    assert body["date"] == "2026-06-15"
    assert body["start_time"] is None
    assert body["end_time"] is None


@pytest.mark.asyncio
async def test_delete_my_exception(
    client, db_session, staff_user, linked_staff, settings
) -> None:
    from app.db.enums import ScheduleExceptionType
    from app.db.models.schedule import ScheduleException
    from datetime import date as date_t
    exc = ScheduleException(
        staff_id=linked_staff.id,
        date=date_t(2026, 6, 20),
        type=ScheduleExceptionType.DAY_OFF,
    )
    db_session.add(exc)
    await db_session.commit()
    await db_session.refresh(exc)

    res = await client.delete(
        f"/api/v1/staff/me/exceptions/{exc.id}",
        headers=auth_headers(staff_user, settings),
    )
    assert res.status_code == 204


@pytest.mark.asyncio
async def test_delete_other_staff_exception_404(
    client, db_session, business, staff_user, linked_staff, settings
) -> None:
    other = StaffMember(
        business_id=business.id, branch_id=business._default_branch_id, name="Other"
    )
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)
    from app.db.enums import ScheduleExceptionType
    from app.db.models.schedule import ScheduleException
    from datetime import date as date_t
    exc = ScheduleException(
        staff_id=other.id,
        date=date_t(2026, 6, 21),
        type=ScheduleExceptionType.DAY_OFF,
    )
    db_session.add(exc)
    await db_session.commit()
    await db_session.refresh(exc)

    res = await client.delete(
        f"/api/v1/staff/me/exceptions/{exc.id}",
        headers=auth_headers(staff_user, settings),
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_unlinked_working_hours_put_403(client, staff_user, settings) -> None:
    res = await client.put(
        "/api/v1/staff/me/working-hours",
        json={"entries": []},
        headers=auth_headers(staff_user, settings),
    )
    assert res.status_code == 403
