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
