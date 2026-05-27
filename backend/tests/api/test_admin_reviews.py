from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.db.enums import BookingStatus
from app.db.models.booking import Booking
from app.db.models.review import Review
from app.db.models.service import Service
from app.db.models.staff import StaffMember
from tests.conftest import auth_headers


async def _seed_review(db_session, business, client_user) -> Review:
    svc = Service(
        business_id=business.id, branch_id=business._default_branch_id,
        title="S", duration_minutes=30,
    )
    db_session.add(svc)
    staff = StaffMember(business_id=business.id, branch_id=business._default_branch_id, name="M")
    db_session.add(staff)
    await db_session.flush()
    starts = datetime.now(UTC) - timedelta(hours=4)
    bk = Booking(
        business_id=business.id, branch_id=business._default_branch_id,
        client_id=client_user.id, staff_id=staff.id, service_id=svc.id,
        starts_at=starts, ends_at=starts + timedelta(minutes=30),
        status=BookingStatus.COMPLETED,
    )
    db_session.add(bk)
    await db_session.flush()
    r = Review(
        booking_id=bk.id, client_id=client_user.id,
        service_id=svc.id, staff_id=staff.id, rating=3, text="ok",
    )
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)
    return r


@pytest.mark.asyncio
async def test_admin_list_includes_all(
    client, db_session, business, client_user, admin_user, settings
) -> None:
    r = await _seed_review(db_session, business, client_user)
    res = await client.get(
        "/api/v1/admin/reviews",
        headers=auth_headers(admin_user, settings),
    )
    assert res.status_code == 200, res.text
    ids = [row["id"] for row in res.json()]
    assert r.id in ids


@pytest.mark.asyncio
async def test_admin_hide_unhide(
    client, db_session, business, client_user, admin_user, settings
) -> None:
    r = await _seed_review(db_session, business, client_user)
    h = await client.post(
        f"/api/v1/admin/reviews/{r.id}/hide",
        headers=auth_headers(admin_user, settings),
    )
    assert h.status_code == 200
    await db_session.refresh(r)
    assert r.is_hidden is True

    u = await client.post(
        f"/api/v1/admin/reviews/{r.id}/unhide",
        headers=auth_headers(admin_user, settings),
    )
    assert u.status_code == 200
    await db_session.refresh(r)
    assert r.is_hidden is False


@pytest.mark.asyncio
async def test_admin_reply_persists(
    client, db_session, business, client_user, admin_user, settings
) -> None:
    r = await _seed_review(db_session, business, client_user)
    res = await client.post(
        f"/api/v1/admin/reviews/{r.id}/reply",
        json={"text": "Спасибо за отзыв!"},
        headers=auth_headers(admin_user, settings),
    )
    assert res.status_code == 200, res.text
    await db_session.refresh(r)
    assert r.admin_reply == "Спасибо за отзыв!"
    assert r.admin_reply_user_id == admin_user.id


@pytest.mark.asyncio
async def test_admin_delete_review_recomputes_aggregates(
    client, db_session, business, client_user, admin_user, settings
) -> None:
    from app.services.reviews_service import ReviewsService
    r = await _seed_review(db_session, business, client_user)
    await ReviewsService(db_session).recompute_aggregates(
        service_id=r.service_id, staff_id=r.staff_id
    )
    await db_session.commit()
    svc = await db_session.get(Service, r.service_id)
    assert svc.review_count == 1

    res = await client.delete(
        f"/api/v1/admin/reviews/{r.id}",
        headers=auth_headers(admin_user, settings),
    )
    assert res.status_code == 204
    await db_session.refresh(svc)
    assert svc.review_count == 0
    assert svc.avg_rating is None
