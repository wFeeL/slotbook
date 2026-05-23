import pytest

from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_put_then_get_working_hours_round_trip(
    client, db_session, business, admin_user, settings
) -> None:
    from app.db.models.staff import StaffMember

    staff = StaffMember(business_id=business.id, branch_id=business._default_branch_id, name="Eve")
    db_session.add(staff)
    await db_session.commit()
    await db_session.refresh(staff)

    put = await client.put(
        f"/api/v1/admin/staff/{staff.id}/working-hours",
        json={
            "entries": [
                {"weekday": 0, "start_time": "10:00:00", "end_time": "18:00:00", "is_active": True},
                {"weekday": 1, "start_time": "10:00:00", "end_time": "18:00:00", "is_active": True},
                {
                    "weekday": 2,
                    "start_time": "10:00:00",
                    "end_time": "14:00:00",
                    "is_active": False,
                },
            ]
        },
        headers=auth_headers(admin_user, settings),
    )
    assert put.status_code == 204

    get = await client.get(
        f"/api/v1/admin/staff/{staff.id}/working-hours",
        headers=auth_headers(admin_user, settings),
    )
    assert get.status_code == 200
    rows = get.json()
    assert {r["weekday"] for r in rows} == {0, 1, 2}
    assert [r["is_active"] for r in rows if r["weekday"] == 2] == [False]


@pytest.mark.asyncio
async def test_put_working_hours_replaces_atomically(
    client, db_session, business, admin_user, settings
) -> None:
    from app.db.models.staff import StaffMember

    staff = StaffMember(business_id=business.id, branch_id=business._default_branch_id, name="Eve")
    db_session.add(staff)
    await db_session.commit()
    await db_session.refresh(staff)

    headers = auth_headers(admin_user, settings)
    await client.put(
        f"/api/v1/admin/staff/{staff.id}/working-hours",
        json={
            "entries": [
                {"weekday": d, "start_time": "10:00:00", "end_time": "18:00:00", "is_active": True}
                for d in range(7)
            ]
        },
        headers=headers,
    )
    await client.put(
        f"/api/v1/admin/staff/{staff.id}/working-hours",
        json={
            "entries": [
                {"weekday": 0, "start_time": "09:00:00", "end_time": "17:00:00", "is_active": True}
            ]
        },
        headers=headers,
    )
    rows = (
        await client.get(f"/api/v1/admin/staff/{staff.id}/working-hours", headers=headers)
    ).json()
    assert len(rows) == 1
    assert rows[0]["weekday"] == 0


@pytest.mark.asyncio
async def test_create_and_delete_day_off_exception(
    client, db_session, business, admin_user, settings
) -> None:
    from app.db.models.staff import StaffMember

    staff = StaffMember(business_id=business.id, branch_id=business._default_branch_id, name="Eve")
    db_session.add(staff)
    await db_session.commit()
    await db_session.refresh(staff)

    headers = auth_headers(admin_user, settings)
    create = await client.post(
        f"/api/v1/admin/staff/{staff.id}/exceptions",
        json={"date": "2026-12-31", "type": "day_off"},
        headers=headers,
    )
    assert create.status_code == 201
    exc_id = create.json()["id"]
    assert create.json()["start_time"] is None

    delete = await client.delete(
        f"/api/v1/admin/staff/{staff.id}/exceptions/{exc_id}",
        headers=headers,
    )
    assert delete.status_code == 204
