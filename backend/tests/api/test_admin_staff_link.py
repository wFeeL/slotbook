from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.enums import UserRole
from app.db.models.staff import StaffMember
from app.db.models.user import User


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
