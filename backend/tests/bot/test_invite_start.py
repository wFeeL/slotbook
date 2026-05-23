"""Bot /start invite_<token> deep-link flow tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.db.enums import UserRole
from app.db.models.admin_invite import AdminInvite
from app.db.models.user import User
from tests.bot.conftest import make_message_update


@pytest_asyncio.fixture
async def active_invite(db_session, business, admin_user) -> AdminInvite:
    invite = AdminInvite(
        business_id=business.id,
        token="valid-token-abc",
        role=UserRole.ADMIN.value,
        created_by_user_id=admin_user.id,
        expires_at=datetime.now(UTC) + timedelta(hours=24),
    )
    db_session.add(invite)
    await db_session.commit()
    await db_session.refresh(invite)
    return invite


@pytest_asyncio.fixture
async def expired_invite(db_session, business, admin_user) -> AdminInvite:
    invite = AdminInvite(
        business_id=business.id,
        token="expired-token-xyz",
        role=UserRole.ADMIN.value,
        created_by_user_id=admin_user.id,
        expires_at=datetime.now(UTC) - timedelta(hours=1),
    )
    db_session.add(invite)
    await db_session.commit()
    await db_session.refresh(invite)
    return invite


@pytest_asyncio.fixture
async def consumed_invite(db_session, business, admin_user) -> AdminInvite:
    now = datetime.now(UTC)
    invite = AdminInvite(
        business_id=business.id,
        token="consumed-token-qqq",
        role=UserRole.ADMIN.value,
        created_by_user_id=admin_user.id,
        expires_at=now + timedelta(hours=24),
        consumed_at=now - timedelta(minutes=5),
        consumed_by_user_id=admin_user.id,
    )
    db_session.add(invite)
    await db_session.commit()
    await db_session.refresh(invite)
    return invite


@pytest.mark.asyncio
async def test_valid_invite_promotes_user_to_admin(
    feed, db_session, mock_bot, active_invite
) -> None:
    token = active_invite.token
    invite_id = active_invite.id
    update = make_message_update(
        f"/start invite_{token}",
        from_user_id=77701,
        from_user_first_name="Newbie",
    )
    await feed(update)

    db_session.sync_session.expire_all()
    user = (
        await db_session.execute(select(User).where(User.telegram_id == 77701))
    ).scalar_one()
    assert user.role == UserRole.ADMIN

    invite = (
        await db_session.execute(
            select(AdminInvite).where(AdminInvite.id == invite_id)
        )
    ).scalar_one()
    assert invite.consumed_at is not None
    assert invite.consumed_by_user_id == user.id


@pytest.mark.asyncio
async def test_expired_invite_is_rejected(
    feed, db_session, mock_bot, expired_invite
) -> None:
    token = expired_invite.token
    invite_id = expired_invite.id
    update = make_message_update(
        f"/start invite_{token}",
        from_user_id=77702,
        from_user_first_name="Late",
    )
    await feed(update)

    db_session.sync_session.expire_all()
    user = (
        await db_session.execute(select(User).where(User.telegram_id == 77702))
    ).scalar_one()
    # Not promoted — stays CLIENT.
    assert user.role == UserRole.CLIENT

    invite = (
        await db_session.execute(
            select(AdminInvite).where(AdminInvite.id == invite_id)
        )
    ).scalar_one()
    assert invite.consumed_at is None


@pytest.mark.asyncio
async def test_already_consumed_invite_is_rejected(
    feed, db_session, mock_bot, consumed_invite
) -> None:
    token = consumed_invite.token
    invite_id = consumed_invite.id
    original_consumer = consumed_invite.consumed_by_user_id
    update = make_message_update(
        f"/start invite_{token}",
        from_user_id=77703,
        from_user_first_name="Toolate",
    )
    await feed(update)

    db_session.sync_session.expire_all()
    user = (
        await db_session.execute(select(User).where(User.telegram_id == 77703))
    ).scalar_one()
    assert user.role == UserRole.CLIENT

    invite = (
        await db_session.execute(
            select(AdminInvite).where(AdminInvite.id == invite_id)
        )
    ).scalar_one()
    # consumed_by_user_id not overwritten
    assert invite.consumed_by_user_id == original_consumer


@pytest.mark.asyncio
async def test_invalid_token_is_rejected(feed, db_session, mock_bot, business) -> None:
    update = make_message_update(
        "/start invite_doesnotexist",
        from_user_id=77704,
        from_user_first_name="Phisher",
    )
    await feed(update)

    db_session.sync_session.expire_all()
    user = (
        await db_session.execute(select(User).where(User.telegram_id == 77704))
    ).scalar_one()
    assert user.role == UserRole.CLIENT
