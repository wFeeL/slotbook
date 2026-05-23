from datetime import UTC, datetime, time, timedelta

import pytest
from sqlalchemy import select

from app.db.enums import (
    NotificationStatus,
    NotificationType,
)
from app.db.models.notification import Notification
from app.db.models.schedule import WorkingHours
from app.db.models.service import Service
from app.db.models.staff import StaffMember, StaffService
from tests.conftest import auth_headers


@pytest.fixture
async def booking_setup(db_session, business):  # type: ignore[no-untyped-def]
    branch_id = business._default_branch_id
    svc = Service(business_id=business.id, branch_id=branch_id, title="Cut", duration_minutes=60)
    staff = StaffMember(business_id=business.id, branch_id=branch_id, name="Eve")
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
    return {"service_id": svc.id, "staff_id": staff.id}


def _future_iso() -> str:
    dt = (datetime.now(UTC) + timedelta(days=2)).replace(hour=12, minute=0, second=0, microsecond=0)
    return dt.isoformat()


async def test_create_booking_dispatches_client_notification_as_sent(
    client, db_session, client_user, settings, booking_setup
) -> None:
    body = {
        "service_id": booking_setup["service_id"],
        "staff_id": booking_setup["staff_id"],
        "starts_at": _future_iso(),
    }
    response = await client.post(
        "/api/v1/bookings", json=body, headers=auth_headers(client_user, settings)
    )
    assert response.status_code == 201, response.text
    booking_id = response.json()["id"]

    db_session.sync_session.expire_all()
    notifs = (
        (
            await db_session.execute(
                select(Notification).where(Notification.booking_id == booking_id)
            )
        )
        .scalars()
        .all()
    )

    client_notifs = [
        n for n in notifs if n.notification_type == NotificationType.BOOKING_CREATED_CLIENT
    ]
    assert len(client_notifs) == 1
    assert client_notifs[0].notification_status == NotificationStatus.SENT
    assert client_notifs[0].sent_at is not None


async def test_cancel_booking_dispatches_cancellation_notification(
    client, db_session, client_user, settings, booking_setup
) -> None:
    body = {
        "service_id": booking_setup["service_id"],
        "staff_id": booking_setup["staff_id"],
        "starts_at": _future_iso(),
    }
    headers = auth_headers(client_user, settings)
    create_resp = await client.post("/api/v1/bookings", json=body, headers=headers)
    booking_id = create_resp.json()["id"]

    cancel_resp = await client.post(f"/api/v1/bookings/{booking_id}/cancel", headers=headers)
    assert cancel_resp.status_code == 200

    db_session.sync_session.expire_all()
    cancel_notifs = (
        (
            await db_session.execute(
                select(Notification).where(
                    Notification.booking_id == booking_id,
                    Notification.notification_type == NotificationType.BOOKING_CANCELLED_CLIENT,
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(cancel_notifs) == 1
    assert cancel_notifs[0].notification_status == NotificationStatus.SENT
