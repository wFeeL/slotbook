from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.review import Review


class ReviewsRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, review: Review) -> None:
        self.session.add(review)

    async def get(self, review_id: int) -> Review | None:
        return await self.session.get(Review, review_id)

    async def get_by_booking(self, booking_id: int) -> Review | None:
        stmt = select(Review).where(Review.booking_id == booking_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_public_for_service(
        self, service_id: int, *, limit: int = 20, offset: int = 0
    ) -> list[Review]:
        stmt = (
            select(Review)
            .where(Review.service_id == service_id, Review.is_hidden.is_(False))
            .order_by(Review.created_at.desc())
            .limit(limit).offset(offset)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def list_public_for_staff(
        self, staff_id: int, *, limit: int = 20, offset: int = 0
    ) -> list[Review]:
        stmt = (
            select(Review)
            .where(Review.staff_id == staff_id, Review.is_hidden.is_(False))
            .order_by(Review.created_at.desc())
            .limit(limit).offset(offset)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def list_admin(
        self,
        *,
        hidden: bool | None = None,
        service_id: int | None = None,
        staff_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Review]:
        stmt = select(Review)
        if hidden is True:
            stmt = stmt.where(Review.is_hidden.is_(True))
        elif hidden is False:
            stmt = stmt.where(Review.is_hidden.is_(False))
        if service_id is not None:
            stmt = stmt.where(Review.service_id == service_id)
        if staff_id is not None:
            stmt = stmt.where(Review.staff_id == staff_id)
        stmt = stmt.order_by(Review.created_at.desc()).limit(limit).offset(offset)
        return list((await self.session.execute(stmt)).scalars().all())

    async def aggregate_for_service(self, service_id: int) -> tuple[float | None, int]:
        stmt = select(
            func.avg(Review.rating), func.count(Review.id)
        ).where(Review.service_id == service_id, Review.is_hidden.is_(False))
        row = (await self.session.execute(stmt)).one()
        avg = float(row[0]) if row[0] is not None else None
        return avg, int(row[1])

    async def aggregate_for_staff(self, staff_id: int) -> tuple[float | None, int]:
        stmt = select(
            func.avg(Review.rating), func.count(Review.id)
        ).where(Review.staff_id == staff_id, Review.is_hidden.is_(False))
        row = (await self.session.execute(stmt)).one()
        avg = float(row[0]) if row[0] is not None else None
        return avg, int(row[1])

    async def delete(self, review: Review) -> None:
        await self.session.delete(review)
