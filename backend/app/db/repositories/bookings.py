from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import BookingStatus
from app.db.models.booking import Booking


class BookingsRepo:
    """Methods needed for slot calculation; create/cancel come in Tasks 15-16."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_active_for_staff_range(
        self, staff_id: int, start_utc: datetime, end_utc: datetime
    ) -> list[Booking]:
        stmt = (
            select(Booking)
            .where(
                Booking.staff_id == staff_id,
                Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
                Booking.starts_at < end_utc,
                Booking.ends_at > start_utc,
            )
            .order_by(Booking.starts_at)
        )
        return list((await self.session.execute(stmt)).scalars().all())
