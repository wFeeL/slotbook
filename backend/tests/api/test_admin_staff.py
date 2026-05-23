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


@pytest.mark.asyncio
async def test_admin_list_staff_returns_service_ids(
    client, db_session, business, admin_user, settings
) -> None:
    from app.db.models.service import Service
    from app.db.models.staff import StaffMember, StaffService

    svc1 = Service(business_id=business.id, title="X", duration_minutes=30)
    svc2 = Service(business_id=business.id, title="Y", duration_minutes=60)
    db_session.add_all([svc1, svc2])
    await db_session.flush()

    staff_a = StaffMember(business_id=business.id, name="A", is_active=True)
    staff_b = StaffMember(business_id=business.id, name="B", is_active=False)  # archived
    db_session.add_all([staff_a, staff_b])
    await db_session.flush()

    db_session.add(StaffService(staff_id=staff_a.id, service_id=svc1.id))
    db_session.add(StaffService(staff_id=staff_a.id, service_id=svc2.id))
    await db_session.commit()

    # include_archived=true (default) returns both
    response = await client.get(
        "/api/v1/admin/staff",
        headers=auth_headers(admin_user, settings),
    )
    assert response.status_code == 200, response.text
    data = response.json()
    ids = {row["id"] for row in data}
    assert staff_a.id in ids and staff_b.id in ids

    row_a = next(r for r in data if r["id"] == staff_a.id)
    assert sorted(row_a["service_ids"]) == sorted([svc1.id, svc2.id])
    assert row_a["is_active"] is True

    row_b = next(r for r in data if r["id"] == staff_b.id)
    assert row_b["service_ids"] == []
    assert row_b["is_active"] is False

    # include_archived=false hides archived staff
    response = await client.get(
        "/api/v1/admin/staff?include_archived=false",
        headers=auth_headers(admin_user, settings),
    )
    assert response.status_code == 200
    ids = {row["id"] for row in response.json()}
    assert staff_a.id in ids and staff_b.id not in ids
