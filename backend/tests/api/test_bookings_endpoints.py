"""API tests for POST /api/v1/bookings and POST /api/v1/bookings/{id}/cancel."""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta

import pytest

from tests.conftest import auth_headers


def _future_slot() -> str:
    """Return an ISO8601 UTC datetime string 2 days in the future at 12:00 UTC."""
    base = datetime.now(UTC).replace(hour=12, minute=0, second=0, microsecond=0)
    return (base + timedelta(days=2)).isoformat()


@pytest.fixture
def future_slot_str() -> str:
    return _future_slot()


# ---------------------------------------------------------------------------
# Shared seed helper (not a fixture, just called by tests)
# ---------------------------------------------------------------------------


async def _seed(db_session, business):  # type: ignore[no-untyped-def]
    """Helper: create service + staff + StaffService + 24h working hours for all weekdays."""
    from app.db.models.schedule import WorkingHours
    from app.db.models.service import Service
    from app.db.models.staff import StaffMember, StaffService

    branch_id = business._default_branch_id
    svc = Service(business_id=business.id, branch_id=branch_id, title="Haircut", duration_minutes=60)
    staff = StaffMember(business_id=business.id, branch_id=branch_id, name="Bob")
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


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_booking_succeeds(client, db_session, business, client_user, settings) -> None:  # type: ignore[no-untyped-def]
    svc, staff = await _seed(db_session, business)
    payload = {
        "service_id": svc.id,
        "staff_id": staff.id,
        "starts_at": _future_slot(),
    }
    resp = await client.post(
        "/api/v1/bookings",
        json=payload,
        headers=auth_headers(client_user, settings),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "confirmed"
    assert body["service_id"] == svc.id
    assert body["staff_id"] == staff.id


@pytest.mark.asyncio
async def test_create_booking_on_taken_slot_returns_409(
    client, db_session, business, client_user, settings
) -> None:  # type: ignore[no-untyped-def]
    svc, staff = await _seed(db_session, business)
    payload = {
        "service_id": svc.id,
        "staff_id": staff.id,
        "starts_at": _future_slot(),
    }
    headers = auth_headers(client_user, settings)
    resp1 = await client.post("/api/v1/bookings", json=payload, headers=headers)
    assert resp1.status_code == 201, resp1.text

    resp2 = await client.post("/api/v1/bookings", json=payload, headers=headers)
    assert resp2.status_code == 409, resp2.text
    assert resp2.json()["detail"]["code"] == "slot_already_taken"


@pytest.mark.asyncio
async def test_create_booking_in_past_returns_422(
    client, db_session, business, client_user, settings
) -> None:  # type: ignore[no-untyped-def]
    svc, staff = await _seed(db_session, business)
    past_time = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    payload = {
        "service_id": svc.id,
        "staff_id": staff.id,
        "starts_at": past_time,
    }
    resp = await client.post(
        "/api/v1/bookings",
        json=payload,
        headers=auth_headers(client_user, settings),
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["detail"]["code"] == "slot_in_past"


@pytest.mark.asyncio
async def test_cancel_booking_by_owner(client, db_session, business, client_user, settings) -> None:  # type: ignore[no-untyped-def]
    svc, staff = await _seed(db_session, business)
    headers = auth_headers(client_user, settings)
    create_resp = await client.post(
        "/api/v1/bookings",
        json={"service_id": svc.id, "staff_id": staff.id, "starts_at": _future_slot()},
        headers=headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    booking_id = create_resp.json()["id"]

    cancel_resp = await client.post(
        f"/api/v1/bookings/{booking_id}/cancel",
        headers=headers,
    )
    assert cancel_resp.status_code == 200, cancel_resp.text
    assert cancel_resp.json()["status"] == "cancelled_by_client"


@pytest.mark.asyncio
async def test_cancel_by_non_owner_returns_403(
    client, db_session, business, client_user, admin_user, settings
) -> None:  # type: ignore[no-untyped-def]
    """A different client (not the booking owner) should get 403."""

    from app.db.enums import UserRole
    from app.db.models.user import User

    svc, staff = await _seed(db_session, business)

    # Create a second client user
    other_client = User(
        telegram_id=9999,
        first_name="Other",
        role=UserRole.CLIENT,
        last_seen_at=datetime.now(UTC),
    )
    db_session.add(other_client)
    await db_session.commit()
    await db_session.refresh(other_client)

    owner_headers = auth_headers(client_user, settings)
    other_headers = auth_headers(other_client, settings)

    # Owner creates booking
    create_resp = await client.post(
        "/api/v1/bookings",
        json={"service_id": svc.id, "staff_id": staff.id, "starts_at": _future_slot()},
        headers=owner_headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    booking_id = create_resp.json()["id"]

    # Other client tries to cancel
    cancel_resp = await client.post(
        f"/api/v1/bookings/{booking_id}/cancel",
        headers=other_headers,
    )
    assert cancel_resp.status_code == 403, cancel_resp.text


@pytest.mark.asyncio
async def test_create_booking_at_non_step_time_returns_422(
    client, db_session, business, client_user, settings
) -> None:  # type: ignore[no-untyped-def]
    """Booking at a non-step time (e.g. 12:07 with 15-min steps) should be rejected."""
    # Set slot_step_minutes=15 on the business row
    business.slot_step_minutes = 15
    db_session.add(business)
    await db_session.commit()
    await db_session.refresh(business)

    svc, staff = await _seed(db_session, business)

    # Build a slot that is NOT on a 15-minute boundary: pick the next day at 12:07 UTC
    base = datetime.now(UTC).replace(hour=12, minute=7, second=0, microsecond=0)
    non_step_slot = (base + timedelta(days=2)).isoformat()

    payload = {
        "service_id": svc.id,
        "staff_id": staff.id,
        "starts_at": non_step_slot,
    }
    resp = await client.post(
        "/api/v1/bookings",
        json=payload,
        headers=auth_headers(client_user, settings),
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["detail"]["code"] == "slot_outside_working_hours"


@pytest.mark.asyncio
async def test_create_booking_within_buffer_window_returns_422(
    client, db_session, business, client_user, settings
) -> None:  # type: ignore[no-untyped-def]
    """With buffer_minutes=15 and a 60-min service, the next valid start after 10:00
    is 11:15 (10:00 + 60min + 15min buffer). Booking at 11:00 should be rejected."""
    # Set booking_buffer_minutes=15 and slot_step_minutes=15 on the business row
    business.booking_buffer_minutes = 15
    business.slot_step_minutes = 15
    db_session.add(business)
    await db_session.commit()
    await db_session.refresh(business)

    svc, staff = await _seed(db_session, business)

    # First booking at 10:00 UTC, 2 days from now
    base = datetime.now(UTC).replace(hour=10, minute=0, second=0, microsecond=0)
    slot_10_00 = (base + timedelta(days=2)).isoformat()
    slot_11_00 = (base + timedelta(days=2, hours=1)).isoformat()

    headers = auth_headers(client_user, settings)

    # Create the first booking at 10:00 — should succeed
    resp1 = await client.post(
        "/api/v1/bookings",
        json={"service_id": svc.id, "staff_id": staff.id, "starts_at": slot_10_00},
        headers=headers,
    )
    assert resp1.status_code == 201, resp1.text

    # Attempt second booking at 11:00 — 10:00+60min=11:00, but buffer pushes
    # next valid slot to 11:15; so 11:00 is inside the buffer window
    resp2 = await client.post(
        "/api/v1/bookings",
        json={"service_id": svc.id, "staff_id": staff.id, "starts_at": slot_11_00},
        headers=headers,
    )
    # The FOR UPDATE lock sees no direct overlap (11:00-12:00 doesn't overlap 10:00-11:00),
    # so the buffer check in calculate_available_slots is what catches it -> 422
    assert resp2.status_code == 422, resp2.text
    assert resp2.json()["detail"]["code"] == "slot_outside_working_hours"


@pytest.mark.asyncio
async def test_my_bookings_returns_only_own(
    client, db_session, business, client_user, settings
) -> None:  # type: ignore[no-untyped-def]
    """GET /bookings/my returns only the authenticated user's own bookings."""
    from app.db.enums import UserRole
    from app.db.models.user import User

    svc, staff = await _seed(db_session, business)

    # Create a second client user
    other_client = User(
        telegram_id=8888,
        first_name="Other",
        role=UserRole.CLIENT,
        last_seen_at=datetime.now(UTC),
    )
    db_session.add(other_client)
    await db_session.commit()
    await db_session.refresh(other_client)

    owner_headers = auth_headers(client_user, settings)
    other_headers = auth_headers(other_client, settings)

    # Owner creates a booking
    create_resp = await client.post(
        "/api/v1/bookings",
        json={"service_id": svc.id, "staff_id": staff.id, "starts_at": _future_slot()},
        headers=owner_headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    booking_id = create_resp.json()["id"]

    # Owner's /my returns the booking
    owner_resp = await client.get("/api/v1/bookings/my", headers=owner_headers)
    assert owner_resp.status_code == 200, owner_resp.text
    owner_bookings = owner_resp.json()
    assert any(b["id"] == booking_id for b in owner_bookings)

    # Other client's /my returns empty list
    other_resp = await client.get("/api/v1/bookings/my", headers=other_headers)
    assert other_resp.status_code == 200, other_resp.text
    assert other_resp.json() == []
