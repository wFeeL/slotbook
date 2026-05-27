from __future__ import annotations

from datetime import UTC, datetime

from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import PhotoOwnerType
from app.db.models.photo import Photo
from app.db.models.service import Service
from app.db.models.staff import StaffMember
from app.db.repositories.pending_photo_uploads import PendingPhotoUploadsRepo
from app.db.repositories.photos import PhotosRepo
from app.db.repositories.users import UsersRepo

router = Router(name="upload")


async def _describe_target(
    session: AsyncSession, owner_type: PhotoOwnerType, owner_id: int
) -> str:
    if owner_type == PhotoOwnerType.SERVICE:
        svc = await session.get(Service, owner_id)
        return f'услуги «{svc.title}»' if svc else f"услуги #{owner_id}"
    stf = await session.get(StaffMember, owner_id)
    return f"мастера {stf.name}" if stf else f"мастера #{owner_id}"


@router.message(CommandStart(deep_link=True))
async def on_start_with_payload(
    message: Message, command: CommandObject, session: AsyncSession
) -> None:
    if not command.args or command.args != "upload":
        return
    tg_user = message.from_user
    if tg_user is None:
        return
    db_user = await UsersRepo(session).get_by_telegram_id(tg_user.id)
    if db_user is None:
        await message.answer("⚠ Пользователь не найден.")
        return
    pending = await PendingPhotoUploadsRepo(session).get_for_user(db_user.id)
    now = datetime.now(UTC)
    if pending is None or pending.expires_at <= now:
        await message.answer(
            "⚠ Сначала откройте Mini App, форму услуги или мастера, и нажмите «Загрузить фото»."
        )
        return
    label = await _describe_target(session, pending.owner_type, pending.owner_id)
    await message.answer(f"📷 Пришлите фото для {label} одним сообщением.")


@router.message(F.photo)
async def on_photo(message: Message, session: AsyncSession) -> None:
    tg_user = message.from_user
    if tg_user is None:
        return
    db_user = await UsersRepo(session).get_by_telegram_id(tg_user.id)
    if db_user is None:
        return
    pending = await PendingPhotoUploadsRepo(session).get_for_user(db_user.id)
    now = datetime.now(UTC)
    if pending is None or pending.expires_at <= now:
        return

    tg_photo = message.photo[-1]
    repo = PhotosRepo(session)
    next_sort = await repo.next_sort_order(pending.owner_type, pending.owner_id)
    repo.add(
        Photo(
            owner_type=pending.owner_type,
            owner_id=pending.owner_id,
            telegram_file_id=tg_photo.file_id,
            telegram_file_unique_id=tg_photo.file_unique_id,
            mime_type="image/jpeg",
            width=tg_photo.width,
            height=tg_photo.height,
            sort_order=next_sort,
        )
    )
    await PendingPhotoUploadsRepo(session).delete_for_user(db_user.id)
    await session.commit()
    await message.answer("✅ Фото сохранено. Можно вернуться в Mini App.")
