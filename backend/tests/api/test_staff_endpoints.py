import pytest

from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_list_staff_for_service(client, db_session, business, client_user, settings) -> None:
    from app.db.models.service import Service
    from app.db.models.staff import StaffMember, StaffService

    svc = Service(business_id=business.id, title="Cut", duration_minutes=60)
    s1 = StaffMember(business_id=business.id, name="Alice")
    s2 = StaffMember(business_id=business.id, name="Bob")
    s3 = StaffMember(business_id=business.id, name="Carol")  # not linked
    db_session.add_all([svc, s1, s2, s3])
    await db_session.flush()
    db_session.add_all(
        [
            StaffService(staff_id=s1.id, service_id=svc.id),
            StaffService(staff_id=s2.id, service_id=svc.id),
        ]
    )
    await db_session.commit()

    response = await client.get(
        f"/api/v1/staff?service_id={svc.id}",
        headers=auth_headers(client_user, settings),
    )
    assert response.status_code == 200
    names = sorted(s["name"] for s in response.json())
    assert names == ["Alice", "Bob"]
