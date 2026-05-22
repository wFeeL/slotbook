import pytest

from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_admin_create_and_replace_services(
    client, db_session, business, admin_user, settings
) -> None:
    from app.db.models.service import Service

    svc1 = Service(business_id=business.id, title="A", duration_minutes=30)
    svc2 = Service(business_id=business.id, title="B", duration_minutes=60)
    db_session.add_all([svc1, svc2])
    await db_session.commit()

    create = await client.post(
        "/api/v1/admin/staff",
        json={"name": "Eve"},
        headers=auth_headers(admin_user, settings),
    )
    assert create.status_code == 201
    sid = create.json()["id"]

    put = await client.put(
        f"/api/v1/admin/staff/{sid}/services",
        json={"service_ids": [svc1.id, svc2.id]},
        headers=auth_headers(admin_user, settings),
    )
    assert put.status_code == 204

    listing = await client.get(
        f"/api/v1/staff?service_id={svc1.id}",
        headers=auth_headers(admin_user, settings),
    )
    assert any(s["id"] == sid for s in listing.json())


@pytest.mark.asyncio
async def test_admin_delete_soft_deletes(
    client, db_session, business, admin_user, settings
) -> None:
    from app.db.models.staff import StaffMember

    staff = StaffMember(business_id=business.id, name="Tmp")
    db_session.add(staff)
    await db_session.commit()
    await db_session.refresh(staff)

    response = await client.delete(
        f"/api/v1/admin/staff/{staff.id}",
        headers=auth_headers(admin_user, settings),
    )
    assert response.status_code == 204
    await db_session.refresh(staff)
    assert staff.is_active is False
