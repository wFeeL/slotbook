from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import PhotoOwnerType
from app.db.models.photo import Photo


class PhotosRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, photo: Photo) -> None:
        self.session.add(photo)

    async def get(self, photo_id: int) -> Photo | None:
        return await self.session.get(Photo, photo_id)

    async def list_for_owner(
        self, owner_type: PhotoOwnerType, owner_id: int
    ) -> list[Photo]:
        stmt = (
            select(Photo)
            .where(Photo.owner_type == owner_type, Photo.owner_id == owner_id)
            .order_by(Photo.sort_order, Photo.id)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def list_for_owners(
        self, owner_type: PhotoOwnerType, owner_ids: list[int]
    ) -> dict[int, list[Photo]]:
        if not owner_ids:
            return {}
        stmt = (
            select(Photo)
            .where(Photo.owner_type == owner_type, Photo.owner_id.in_(owner_ids))
            .order_by(Photo.owner_id, Photo.sort_order, Photo.id)
        )
        out: dict[int, list[Photo]] = {oid: [] for oid in owner_ids}
        for row in (await self.session.execute(stmt)).scalars().all():
            out.setdefault(row.owner_id, []).append(row)
        return out

    async def next_sort_order(
        self, owner_type: PhotoOwnerType, owner_id: int
    ) -> int:
        stmt = select(func.coalesce(func.max(Photo.sort_order), -1)).where(
            Photo.owner_type == owner_type, Photo.owner_id == owner_id
        )
        return int((await self.session.execute(stmt)).scalar_one()) + 1

    async def delete(self, photo: Photo) -> None:
        await self.session.delete(photo)
