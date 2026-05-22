from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import BookingStatus
from app.db.models.booking import Booking


class BookingsRepo:
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

    async def find_overlapping_for_update(
        self,
        staff_id: int,
        start_utc: datetime,
        end_utc: datetime,
    ) -> list[Booking]:
        """SELECT ... FOR UPDATE on active bookings that overlap [start_utc, end_utc).

        Acquires row-level locks on any overlapping PENDING|CONFIRMED booking.
        Returns overlapping rows — if any are present, the slot is already taken.
        """
        stmt = (
            select(Booking)
            .where(
                Booking.staff_id == staff_id,
                Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
                Booking.starts_at < end_utc,
                Booking.ends_at > start_utc,
            )
            .with_for_update()
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def get(self, booking_id: int) -> Booking | None:
        return await self.session.get(Booking, booking_id)

    def add(self, booking: Booking) -> None:
        self.session.add(booking)

    async def list_for_client(
        self,
        client_id: int,
        *,
        status: BookingStatus | None = None,
    ) -> list[Booking]:
        stmt = (
            select(Booking).where(Booking.client_id == client_id).order_by(Booking.starts_at.desc())
        )
        if status is not None:
            stmt = stmt.where(Booking.status == status)
        return list((await self.session.execute(stmt)).scalars().all())
