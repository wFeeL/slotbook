"""API tests for admin booking endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta

import pytest

from tests.conftest import auth_headers


def _future() -> str:
    """Return an ISO8601 UTC datetime 2 days in the future at 12:00."""
    base = datetime.now(UTC).replace(hour=12, minute=0, second=0, microsecond=0)
    return (base + timedelta(days=2)).isoformat()


@pytest.fixture
async def setup(db_session, business):  # type: ignore[no-untyped-def]
    """Create service + staff + working hours (00:00-23:00 all weekdays)."""
    from app.db.models.schedule import WorkingHours
    from app.db.models.service import Service
    from app.db.models.staff import StaffMember, StaffService

    branch_id = business._default_branch_id
    svc = Service(business_id=business.id, branch_id=branch_id, title="Test Service", duration_minutes=60)
    staff = StaffMember(business_id=business.id, branch_id=branch_id, name="Test Staff")
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
    await db_session.commit()
    return svc, staff


@pytest.mark.asyncio
async def test_admin_creates_booking_for_new_client_by_telegram_id(
    client, db_session, business, admin_user, setup, settings
) -> None:  # type: ignore[no-untyped-def]
    svc, staff = setup
    new_telegram_id = 555_999_111

    payload = {
        "client_telegram_id": new_telegram_id,
        "service_id": svc.id,
        "staff_id": staff.id,
        "starts_at": _future(),
        "admin_comment": "VIP client",
    }
    resp = await client.post(
        "/api/v1/admin/bookings",
        json=payload,
        headers=auth_headers(admin_user, settings),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["admin_comment"] == "VIP client"
    assert body["status"] == "confirmed"


@pytest.mark.asyncio
async def test_admin_lists_bookings_and_filters_by_status(
    client, db_session, business, client_user, admin_user, setup, settings
) -> None:  # type: ignore[no-untyped-def]
    svc, staff = setup

    # Client creates booking
    create_resp = await client.post(
        "/api/v1/bookings",
        json={"service_id": svc.id, "staff_id": staff.id, "starts_at": _future()},
        headers=auth_headers(client_user, settings),
    )
    assert create_resp.status_code == 201, create_resp.text
    booking_id = create_resp.json()["id"]

    # Admin lists with status=confirmed filter
    list_resp = await client.get(
        "/api/v1/admin/bookings?status=confirmed",
        headers=auth_headers(admin_user, settings),
    )
    assert list_resp.status_code == 200, list_resp.text
    bookings = list_resp.json()
    assert any(b["id"] == booking_id for b in bookings)


@pytest.mark.asyncio
async def test_admin_cancel_bypasses_min_cancellation_window(
    client, db_session, business, client_user, admin_user, setup, settings
) -> None:  # type: ignore[no-untyped-def]
    """Admin cancel succeeds even when min_cancellation_hours is large."""
    svc, staff = setup

    # Set a very large cancellation window on business
    business.min_cancellation_hours = 9999
    db_session.add(business)
    await db_session.commit()

    create_resp = await client.post(
        "/api/v1/bookings",
        json={"service_id": svc.id, "staff_id": staff.id, "starts_at": _future()},
        headers=auth_headers(client_user, settings),
    )
    assert create_resp.status_code == 201, create_resp.text
    booking_id = create_resp.json()["id"]

    cancel_resp = await client.post(
        f"/api/v1/admin/bookings/{booking_id}/cancel",
        headers=auth_headers(admin_user, settings),
    )
    assert cancel_resp.status_code == 200, cancel_resp.text
    assert cancel_resp.json()["status"] == "cancelled_by_admin"


@pytest.mark.asyncio
async def test_admin_patch_only_completed_or_no_show(
    client, db_session, business, client_user, admin_user, setup, settings
) -> None:  # type: ignore[no-untyped-def]
    svc, staff = setup

    create_resp = await client.post(
        "/api/v1/bookings",
        json={"service_id": svc.id, "staff_id": staff.id, "starts_at": _future()},
        headers=auth_headers(client_user, settings),
    )
    assert create_resp.status_code == 201, create_resp.text
    booking_id = create_resp.json()["id"]

    # Patch to completed succeeds
    patch_ok = await client.patch(
        f"/api/v1/admin/bookings/{booking_id}",
        json={"status": "completed"},
        headers=auth_headers(admin_user, settings),
    )
    assert patch_ok.status_code == 200, patch_ok.text
    assert patch_ok.json()["status"] == "completed"

    # Patch to cancelled_by_admin fails with 422
    patch_bad = await client.patch(
        f"/api/v1/admin/bookings/{booking_id}",
        json={"status": "cancelled_by_admin"},
        headers=auth_headers(admin_user, settings),
    )
    assert patch_bad.status_code == 422, patch_bad.text
    assert patch_bad.json()["detail"]["code"] == "cannot_cancel_in_current_status"
