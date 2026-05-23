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
