from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import PhotoOwnerType
from app.db.models.pending_photo_upload import PendingPhotoUpload

DEFAULT_TTL = timedelta(minutes=10)


class PendingPhotoUploadsRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_for_user(self, admin_user_id: int) -> PendingPhotoUpload | None:
        stmt = select(PendingPhotoUpload).where(
            PendingPhotoUpload.admin_user_id == admin_user_id
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def upsert(
        self,
        *,
        admin_user_id: int,
        owner_type: PhotoOwnerType,
        owner_id: int,
        ttl: timedelta = DEFAULT_TTL,
    ) -> PendingPhotoUpload:
        now = datetime.now(UTC)
        await self.session.execute(
            delete(PendingPhotoUpload).where(
                PendingPhotoUpload.admin_user_id == admin_user_id
            )
        )
        intent = PendingPhotoUpload(
            admin_user_id=admin_user_id,
            owner_type=owner_type,
            owner_id=owner_id,
            expires_at=now + ttl,
        )
        self.session.add(intent)
        await self.session.flush()
        return intent

    async def delete_for_user(self, admin_user_id: int) -> None:
        await self.session.execute(
            delete(PendingPhotoUpload).where(
                PendingPhotoUpload.admin_user_id == admin_user_id
            )
        )
