from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_linked_staff
from app.core.errors import Forbidden
from app.db.enums import UserRole
from app.db.models.staff import StaffMember
from app.db.models.user import User
from app.db.repositories.staff import StaffRepo


@pytest.mark.asyncio
async def test_two_active_staff_cannot_share_user_id(db_session, business) -> None:
    user = User(telegram_id=9001, first_name="Mast", role=UserRole.STAFF)
    db_session.add(user)
    await db_session.flush()

    staff_a = StaffMember(
        business_id=business.id,
        branch_id=business._default_branch_id,
        name="A",
        user_id=user.id,
        is_active=True,
    )
    db_session.add(staff_a)
    await db_session.commit()

    staff_b = StaffMember(
        business_id=business.id,
        branch_id=business._default_branch_id,
        name="B",
        user_id=user.id,
        is_active=True,
    )
    db_session.add(staff_b)
    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_one_active_one_archived_can_share_user_id(db_session, business) -> None:
    user = User(telegram_id=9002, first_name="Mast2", role=UserRole.STAFF)
    db_session.add(user)
    await db_session.flush()

    staff_old = StaffMember(
        business_id=business.id,
        branch_id=business._default_branch_id,
        name="Old",
        user_id=user.id,
        is_active=False,
    )
    staff_new = StaffMember(
        business_id=business.id,
        branch_id=business._default_branch_id,
        name="New",
        user_id=user.id,
        is_active=True,
    )
    db_session.add_all([staff_old, staff_new])
    await db_session.commit()


@pytest.mark.asyncio
async def test_repo_get_active_by_user_id_returns_active(db_session, business) -> None:
    user = User(telegram_id=9101, first_name="L", role=UserRole.STAFF)
    db_session.add(user)
    await db_session.flush()
    staff = StaffMember(
        business_id=business.id,
        branch_id=business._default_branch_id,
        name="Linked",
        user_id=user.id,
        is_active=True,
    )
    db_session.add(staff)
    await db_session.commit()

    found = await StaffRepo(db_session).get_active_by_user_id(user.id)
    assert found is not None
    assert found.id == staff.id


@pytest.mark.asyncio
async def test_repo_get_active_by_user_id_ignores_archived(db_session, business) -> None:
    user = User(telegram_id=9102, first_name="A", role=UserRole.STAFF)
    db_session.add(user)
    await db_session.flush()
    staff = StaffMember(
        business_id=business.id,
        branch_id=business._default_branch_id,
        name="Archived",
        user_id=user.id,
        is_active=False,
    )
    db_session.add(staff)
    await db_session.commit()

    found = await StaffRepo(db_session).get_active_by_user_id(user.id)
    assert found is None


@pytest.mark.asyncio
async def test_get_linked_staff_returns_when_linked(db_session, business) -> None:
    user = User(telegram_id=9201, first_name="L", role=UserRole.STAFF)
    db_session.add(user)
    await db_session.flush()
    staff = StaffMember(
        business_id=business.id,
        branch_id=business._default_branch_id,
        name="L",
        user_id=user.id,
        is_active=True,
    )
    db_session.add(staff)
    await db_session.commit()
    await db_session.refresh(user)

    got = await get_linked_staff(user=user, session=db_session)
    assert got.id == staff.id


@pytest.mark.asyncio
async def test_get_linked_staff_raises_when_unlinked(db_session) -> None:
    user = User(telegram_id=9202, first_name="U", role=UserRole.STAFF)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    with pytest.raises(Forbidden):
        await get_linked_staff(user=user, session=db_session)


# ---------------------------------------------------------------------------
# PATCH /admin/staff/:id  user_id linking
# ---------------------------------------------------------------------------

from tests.conftest import auth_headers  # noqa: E402


@pytest.mark.asyncio
async def test_admin_patch_staff_links_user(
    client, db_session, business, admin_user, settings
) -> None:
    staff = StaffMember(
        business_id=business.id, branch_id=business._default_branch_id, name="X"
    )
    target = User(telegram_id=5005, first_name="T", role=UserRole.STAFF)
    db_session.add_all([staff, target])
    await db_session.commit()
    await db_session.refresh(staff)
    await db_session.refresh(target)

    res = await client.patch(
        f"/api/v1/admin/staff/{staff.id}",
        json={"user_id": target.id},
        headers=auth_headers(admin_user, settings),
    )
    assert res.status_code == 200, res.text
    assert res.json()["user_id"] == target.id


@pytest.mark.asyncio
async def test_admin_patch_staff_unlink_user(
    client, db_session, business, admin_user, settings
) -> None:
    target = User(telegram_id=5006, first_name="T", role=UserRole.STAFF)
    db_session.add(target)
    await db_session.flush()
    staff = StaffMember(
        business_id=business.id,
        branch_id=business._default_branch_id,
        name="X",
        user_id=target.id,
    )
    db_session.add(staff)
    await db_session.commit()
    await db_session.refresh(staff)

    res = await client.patch(
        f"/api/v1/admin/staff/{staff.id}",
        json={"user_id": None},
        headers=auth_headers(admin_user, settings),
    )
    assert res.status_code == 200, res.text
    assert res.json()["user_id"] is None


@pytest.mark.asyncio
async def test_admin_patch_staff_rejects_client_role(
    client, db_session, business, admin_user, client_user, settings
) -> None:
    staff = StaffMember(
        business_id=business.id, branch_id=business._default_branch_id, name="X"
    )
    db_session.add(staff)
    await db_session.commit()
    await db_session.refresh(staff)

    res = await client.patch(
        f"/api/v1/admin/staff/{staff.id}",
        json={"user_id": client_user.id},
        headers=auth_headers(admin_user, settings),
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_admin_create_staff_with_user_id_links(
    client, db_session, business, admin_user, settings
) -> None:
    target = User(telegram_id=5101, first_name="T", role=UserRole.STAFF)
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(target)

    res = await client.post(
        "/api/v1/admin/staff",
        json={"name": "New", "user_id": target.id},
        headers=auth_headers(admin_user, settings),
    )
    assert res.status_code == 201, res.text
    assert res.json()["user_id"] == target.id


@pytest.mark.asyncio
async def test_admin_create_staff_rejects_client_user_id(
    client, db_session, business, admin_user, client_user, settings
) -> None:
    res = await client.post(
        "/api/v1/admin/staff",
        json={"name": "New", "user_id": client_user.id},
        headers=auth_headers(admin_user, settings),
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_admin_create_staff_conflict_returns_409(
    client, db_session, business, admin_user, settings
) -> None:
    target = User(telegram_id=5102, first_name="T", role=UserRole.STAFF)
    db_session.add(target)
    await db_session.flush()
    existing = StaffMember(
        business_id=business.id,
        branch_id=business._default_branch_id,
        name="Existing",
        user_id=target.id,
        is_active=True,
    )
    db_session.add(existing)
    await db_session.commit()

    res = await client.post(
        "/api/v1/admin/staff",
        json={"name": "Dup", "user_id": target.id},
        headers=auth_headers(admin_user, settings),
    )
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_admin_patch_staff_conflicting_link_returns_409(
    client, db_session, business, admin_user, settings
) -> None:
    target = User(telegram_id=5007, first_name="T", role=UserRole.STAFF)
    db_session.add(target)
    await db_session.flush()
    staff_a = StaffMember(
        business_id=business.id,
        branch_id=business._default_branch_id,
        name="A",
        user_id=target.id,
    )
    staff_b = StaffMember(
        business_id=business.id, branch_id=business._default_branch_id, name="B"
    )
    db_session.add_all([staff_a, staff_b])
    await db_session.commit()
    await db_session.refresh(staff_b)

    res = await client.patch(
        f"/api/v1/admin/staff/{staff_b.id}",
        json={"user_id": target.id},
        headers=auth_headers(admin_user, settings),
    )
    assert res.status_code == 409
