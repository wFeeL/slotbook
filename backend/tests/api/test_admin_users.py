from __future__ import annotations

import pytest

from app.db.enums import UserRole
from app.db.models.staff import StaffMember
from app.db.models.user import User
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_admin_users_lookup_returns_staff(
    client, db_session, business, admin_user, settings
) -> None:
    u1 = User(telegram_id=6001, first_name="A", role=UserRole.STAFF)
    u2 = User(telegram_id=6002, first_name="B", role=UserRole.CLIENT)
    db_session.add_all([u1, u2])
    await db_session.commit()

    res = await client.get(
        "/api/v1/admin/users?role=staff",
        headers=auth_headers(admin_user, settings),
    )
    assert res.status_code == 200, res.text
    ids = [u["id"] for u in res.json()]
    assert u1.id in ids
    assert u2.id not in ids


@pytest.mark.asyncio
async def test_admin_users_linkable_only_excludes_linked(
    client, db_session, business, admin_user, settings
) -> None:
    u_linked = User(telegram_id=6003, first_name="L", role=UserRole.STAFF)
    u_free = User(telegram_id=6004, first_name="F", role=UserRole.STAFF)
    db_session.add_all([u_linked, u_free])
    await db_session.flush()
    sm = StaffMember(
        business_id=business.id,
        branch_id=business._default_branch_id,
        name="L",
        user_id=u_linked.id,
        is_active=True,
    )
    db_session.add(sm)
    await db_session.commit()

    res = await client.get(
        "/api/v1/admin/users?role=staff&linkable_only=true",
        headers=auth_headers(admin_user, settings),
    )
    assert res.status_code == 200
    ids = [u["id"] for u in res.json()]
    assert u_free.id in ids
    assert u_linked.id not in ids


@pytest.mark.asyncio
async def test_admin_users_linkable_includes_self(
    client, db_session, business, admin_user, settings
) -> None:
    u = User(telegram_id=6005, first_name="X", role=UserRole.STAFF)
    db_session.add(u)
    await db_session.flush()
    sm = StaffMember(
        business_id=business.id,
        branch_id=business._default_branch_id,
        name="X",
        user_id=u.id,
        is_active=True,
    )
    db_session.add(sm)
    await db_session.commit()
    await db_session.refresh(u)

    res = await client.get(
        f"/api/v1/admin/users?role=staff&linkable_only=true&include_user_id={u.id}",
        headers=auth_headers(admin_user, settings),
    )
    assert res.status_code == 200
    ids = [row["id"] for row in res.json()]
    assert u.id in ids


@pytest.mark.asyncio
async def test_admin_users_unauthorized_for_client(
    client, client_user, settings
) -> None:
    res = await client.get(
        "/api/v1/admin/users",
        headers=auth_headers(client_user, settings),
    )
    assert res.status_code == 403
