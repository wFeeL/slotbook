from __future__ import annotations

from datetime import UTC, datetime, time, timedelta

import pytest

from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_slots_smoke(client, db_session, business, branch, client_user, settings) -> None:  # type: ignore[no-untyped-def]
    from app.db.models.schedule import WorkingHours
    from app.db.models.service import Service
    from app.db.models.staff import StaffMember, StaffService

    svc = Service(business_id=business.id, branch_id=branch.id, title="Cut", duration_minutes=60)
    staff = StaffMember(business_id=business.id, branch_id=branch.id, name="Eve")
    db_session.add_all([svc, staff])
    await db_session.flush()
    db_session.add(StaffService(staff_id=staff.id, service_id=svc.id))
    # Add working hours for all 7 weekdays so any future date works
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

    # Pick a date 30 days in the future to bypass the now-filter
    future = (datetime.now(UTC) + timedelta(days=30)).date().isoformat()

    response = await client.get(
        f"/api/v1/slots?service_id={svc.id}&staff_id={staff.id}&date={future}",
        headers=auth_headers(client_user, settings),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["timezone"] == business.timezone
    assert len(body["slots"]) > 0
