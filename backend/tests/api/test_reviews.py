from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.db.enums import BookingStatus, UserRole
from app.db.models.booking import Booking
from app.db.models.review import Review
from app.db.models.service import Service
from app.db.models.staff import StaffMember, StaffService
from app.db.models.user import User
from tests.conftest import auth_headers


async def _completed_booking(db_session, business, client_user) -> Booking:
    svc = Service(
        business_id=business.id, branch_id=business._default_branch_id,
        title="S", duration_minutes=30, price="1000",
    )
    db_session.add(svc)
    await db_session.flush()
    staff = StaffMember(business_id=business.id, branch_id=business._default_branch_id, name="M")
    db_session.add(staff)
    await db_session.flush()
    db_session.add(StaffService(staff_id=staff.id, service_id=svc.id))
    starts = datetime.now(UTC) - timedelta(hours=2)
    bk = Booking(
        business_id=business.id, branch_id=business._default_branch_id,
        client_id=client_user.id, staff_id=staff.id, service_id=svc.id,
        starts_at=starts, ends_at=starts + timedelta(minutes=30),
        status=BookingStatus.COMPLETED,
    )
    db_session.add(bk)
    await db_session.commit()
    await db_session.refresh(bk)
    return bk


@pytest.mark.asyncio
async def test_create_review_happy_path(
    client, db_session, business, client_user, settings
) -> None:
    bk = await _completed_booking(db_session, business, client_user)
    res = await client.post(
        "/api/v1/reviews",
        json={"booking_id": bk.id, "rating": 5, "text": "Огонь!"},
        headers=auth_headers(client_user, settings),
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["rating"] == 5
    assert body["text"] == "Огонь!"

    svc = await db_session.get(Service, bk.service_id)
    await db_session.refresh(svc)
    assert float(svc.avg_rating) == 5.0
    assert svc.review_count == 1


@pytest.mark.asyncio
async def test_create_review_non_completed_422(
    client, db_session, business, client_user, settings
) -> None:
    bk = await _completed_booking(db_session, business, client_user)
    bk.status = BookingStatus.CONFIRMED
    await db_session.commit()

    res = await client.post(
        "/api/v1/reviews",
        json={"booking_id": bk.id, "rating": 5},
        headers=auth_headers(client_user, settings),
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_create_review_other_client_403(
    client, db_session, business, client_user, settings
) -> None:
    bk = await _completed_booking(db_session, business, client_user)
    other = User(telegram_id=8090, first_name="O", role=UserRole.CLIENT)
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)
    res = await client.post(
        "/api/v1/reviews",
        json={"booking_id": bk.id, "rating": 5},
        headers=auth_headers(other, settings),
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_create_review_duplicate_409(
    client, db_session, business, client_user, settings
) -> None:
    bk = await _completed_booking(db_session, business, client_user)
    first = await client.post(
        "/api/v1/reviews",
        json={"booking_id": bk.id, "rating": 5},
        headers=auth_headers(client_user, settings),
    )
    assert first.status_code == 201
    second = await client.post(
        "/api/v1/reviews",
        json={"booking_id": bk.id, "rating": 4},
        headers=auth_headers(client_user, settings),
    )
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_create_review_invalid_rating_422(
    client, db_session, business, client_user, settings
) -> None:
    bk = await _completed_booking(db_session, business, client_user)
    res = await client.post(
        "/api/v1/reviews",
        json={"booking_id": bk.id, "rating": 7},
        headers=auth_headers(client_user, settings),
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_list_public_reviews_for_service_hides_hidden(
    client, db_session, business, client_user, settings
) -> None:
    bk = await _completed_booking(db_session, business, client_user)
    visible = Review(
        booking_id=bk.id, client_id=client_user.id,
        service_id=bk.service_id, staff_id=bk.staff_id,
        rating=5, text="visible", is_hidden=False,
    )
    db_session.add(visible)
    await db_session.commit()

    res = await client.get(
        f"/api/v1/services/{bk.service_id}/reviews",
        headers=auth_headers(client_user, settings),
    )
    assert res.status_code == 200
    items = res.json()
    assert any(r["text"] == "visible" for r in items)

    visible.is_hidden = True
    await db_session.commit()

    res2 = await client.get(
        f"/api/v1/services/{bk.service_id}/reviews",
        headers=auth_headers(client_user, settings),
    )
    assert res2.status_code == 200
    assert all(r["text"] != "visible" for r in res2.json())
