from __future__ import annotations

import pytest

from app.db.enums import UserRole
from app.db.models.staff import StaffMember
from app.db.models.user import User
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_set_member_role_promotes_to_admin(
    client, db_session, admin_user, settings
) -> None:
    target = User(telegram_id=7001, first_name="X", role=UserRole.STAFF)
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)
    res = await client.patch(
        f"/api/v1/admin/team/{target.id}/role",
        json={"role": "admin"},
        headers=auth_headers(admin_user, settings),
    )
    assert res.status_code == 200, res.text
    assert res.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_set_member_role_demote_unlinks_staff(
    client, db_session, business, admin_user, settings
) -> None:
    target = User(telegram_id=7002, first_name="X", role=UserRole.STAFF)
    db_session.add(target)
    await db_session.flush()
    sm = StaffMember(
        business_id=business.id,
        branch_id=business._default_branch_id,
        name="X",
        user_id=target.id,
        is_active=True,
    )
    db_session.add(sm)
    await db_session.commit()
    await db_session.refresh(sm)

    res = await client.patch(
        f"/api/v1/admin/team/{target.id}/role",
        json={"role": "client"},
        headers=auth_headers(admin_user, settings),
    )
    assert res.status_code == 200, res.text
    await db_session.refresh(sm)
    assert sm.user_id is None


@pytest.mark.asyncio
async def test_set_member_role_self_400(
    client, admin_user, settings
) -> None:
    res = await client.patch(
        f"/api/v1/admin/team/{admin_user.id}/role",
        json={"role": "client"},
        headers=auth_headers(admin_user, settings),
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_set_member_role_superadmin_protected(
    client, admin_user, superadmin_user, settings
) -> None:
    res = await client.patch(
        f"/api/v1/admin/team/{superadmin_user.id}/role",
        json={"role": "client"},
        headers=auth_headers(admin_user, settings),
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_remove_member_demotes_to_client(
    client, db_session, business, admin_user, settings
) -> None:
    target = User(telegram_id=7003, first_name="X", role=UserRole.STAFF)
    db_session.add(target)
    await db_session.flush()
    sm = StaffMember(
        business_id=business.id,
        branch_id=business._default_branch_id,
        name="X",
        user_id=target.id,
        is_active=True,
    )
    db_session.add(sm)
    await db_session.commit()
    await db_session.refresh(target)
    await db_session.refresh(sm)

    res = await client.delete(
        f"/api/v1/admin/team/{target.id}",
        headers=auth_headers(admin_user, settings),
    )
    assert res.status_code == 204
    await db_session.refresh(target)
    await db_session.refresh(sm)
    assert target.role == UserRole.CLIENT
    assert sm.user_id is None


@pytest.mark.asyncio
async def test_remove_self_400(client, admin_user, settings) -> None:
    res = await client.delete(
        f"/api/v1/admin/team/{admin_user.id}",
        headers=auth_headers(admin_user, settings),
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_remove_superadmin_403(
    client, admin_user, superadmin_user, settings
) -> None:
    res = await client.delete(
        f"/api/v1/admin/team/{superadmin_user.id}",
        headers=auth_headers(admin_user, settings),
    )
    assert res.status_code == 403
