from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import select

from app.bot.routers.upload import on_photo, on_start_with_payload
from app.db.enums import PhotoOwnerType, UserRole
from app.db.models.pending_photo_upload import PendingPhotoUpload
from app.db.models.photo import Photo
from app.db.models.service import Service
from app.db.models.user import User


def _make_message(tg_id: int, has_photo: bool = False):
    msg = MagicMock()
    msg.from_user = MagicMock(id=tg_id)
    msg.answer = AsyncMock()
    if has_photo:
        photo = MagicMock(
            file_id="FID123", file_unique_id="UID123", width=800, height=600
        )
        msg.photo = [photo]
    else:
        msg.photo = None
    return msg


@pytest.mark.asyncio
async def test_start_with_payload_prompts_when_intent_exists(
    db_session, business
) -> None:
    user = User(telegram_id=4444, first_name="A", role=UserRole.ADMIN)
    svc = Service(
        business_id=business.id, branch_id=business._default_branch_id,
        title="X", duration_minutes=30,
    )
    db_session.add_all([user, svc])
    await db_session.flush()
    intent = PendingPhotoUpload(
        admin_user_id=user.id,
        owner_type=PhotoOwnerType.SERVICE,
        owner_id=svc.id,
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
    )
    db_session.add(intent)
    await db_session.commit()

    msg = _make_message(tg_id=4444)
    command = MagicMock(args="upload")
    await on_start_with_payload(message=msg, command=command, session=db_session)
    msg.answer.assert_awaited_once()
    text = msg.answer.await_args.args[0]
    assert "услуги" in text and "X" in text


@pytest.mark.asyncio
async def test_start_with_payload_warns_when_no_intent(db_session) -> None:
    user = User(telegram_id=4445, first_name="A", role=UserRole.ADMIN)
    db_session.add(user)
    await db_session.commit()

    msg = _make_message(tg_id=4445)
    command = MagicMock(args="upload")
    await on_start_with_payload(message=msg, command=command, session=db_session)
    msg.answer.assert_awaited_once()
    assert "Mini App" in msg.answer.await_args.args[0]


@pytest.mark.asyncio
async def test_photo_attached_to_pending_intent_saves(
    db_session, business
) -> None:
    user = User(telegram_id=4446, first_name="A", role=UserRole.ADMIN)
    svc = Service(
        business_id=business.id, branch_id=business._default_branch_id,
        title="X", duration_minutes=30,
    )
    db_session.add_all([user, svc])
    await db_session.flush()
    db_session.add(PendingPhotoUpload(
        admin_user_id=user.id,
        owner_type=PhotoOwnerType.SERVICE,
        owner_id=svc.id,
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
    ))
    await db_session.commit()

    msg = _make_message(tg_id=4446, has_photo=True)
    await on_photo(message=msg, session=db_session)

    rows = (await db_session.execute(
        select(Photo).where(Photo.owner_id == svc.id)
    )).scalars().all()
    assert len(rows) == 1
    assert rows[0].telegram_file_id == "FID123"
    msg.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_photo_without_intent_silently_ignored(db_session) -> None:
    user = User(telegram_id=4447, first_name="A", role=UserRole.CLIENT)
    db_session.add(user)
    await db_session.commit()

    msg = _make_message(tg_id=4447, has_photo=True)
    await on_photo(message=msg, session=db_session)
    msg.answer.assert_not_awaited()


@pytest.mark.asyncio
async def test_expired_intent_prompts_to_restart(db_session, business) -> None:
    user = User(telegram_id=4448, first_name="A", role=UserRole.ADMIN)
    svc = Service(
        business_id=business.id, branch_id=business._default_branch_id,
        title="X", duration_minutes=30,
    )
    db_session.add_all([user, svc])
    await db_session.flush()
    db_session.add(PendingPhotoUpload(
        admin_user_id=user.id,
        owner_type=PhotoOwnerType.SERVICE,
        owner_id=svc.id,
        expires_at=datetime.now(UTC) - timedelta(minutes=1),
    ))
    await db_session.commit()

    msg = _make_message(tg_id=4448)
    command = MagicMock(args="upload")
    await on_start_with_payload(message=msg, command=command, session=db_session)
    msg.answer.assert_awaited_once()
    assert "Mini App" in msg.answer.await_args.args[0]
