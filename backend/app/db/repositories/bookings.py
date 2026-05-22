from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
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

    async def list_admin(
        self,
        business_id: int,
        *,
        staff_id: int | None = None,
        service_id: int | None = None,
        status: BookingStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Booking]:
        stmt = select(Booking).where(Booking.business_id == business_id)
        if staff_id is not None:
            stmt = stmt.where(Booking.staff_id == staff_id)
        if service_id is not None:
            stmt = stmt.where(Booking.service_id == service_id)
        if status is not None:
            stmt = stmt.where(Booking.status == status)
        stmt = stmt.order_by(Booking.starts_at.desc()).limit(limit).offset(offset)
        return list((await self.session.execute(stmt)).scalars().all())

    async def list_admin_for_local_date(
        self,
        business_id: int,
        start_utc: datetime,
        end_utc: datetime,
        *,
        staff_id: int | None = None,
        service_id: int | None = None,
        status: BookingStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Booking]:
        stmt = select(Booking).where(
            Booking.business_id == business_id,
            Booking.starts_at >= start_utc,
            Booking.starts_at < end_utc,
        )
        if staff_id is not None:
            stmt = stmt.where(Booking.staff_id == staff_id)
        if service_id is not None:
            stmt = stmt.where(Booking.service_id == service_id)
        if status is not None:
            stmt = stmt.where(Booking.status == status)
        stmt = stmt.order_by(Booking.starts_at.asc()).limit(limit).offset(offset)
        return list((await self.session.execute(stmt)).scalars().all())

    async def dashboard_counts(
        self,
        business_id: int,
        today_utc_start: datetime,
        today_utc_end: datetime,
        week_utc_start: datetime,
        week_utc_end: datetime,
        no_show_window_start: datetime,
    ) -> dict[str, int]:
        today_count = (
            await self.session.execute(
                select(func.count())
                .select_from(Booking)
                .where(
                    Booking.business_id == business_id,
                    Booking.starts_at >= today_utc_start,
                    Booking.starts_at < today_utc_end,
                    Booking.status.in_(
                        [BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.COMPLETED]
                    ),
                )
            )
        ).scalar_one()
        week_count = (
            await self.session.execute(
                select(func.count())
                .select_from(Booking)
                .where(
                    Booking.business_id == business_id,
                    Booking.starts_at >= week_utc_start,
                    Booking.starts_at < week_utc_end,
                    Booking.status.in_(
                        [BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.COMPLETED]
                    ),
                )
            )
        ).scalar_one()
        no_show_count = (
            await self.session.execute(
                select(func.count())
                .select_from(Booking)
                .where(
                    Booking.business_id == business_id,
                    Booking.starts_at >= no_show_window_start,
                    Booking.status == BookingStatus.NO_SHOW,
                )
            )
        ).scalar_one()
        return {"today": today_count, "this_week": week_count, "no_show_30d": no_show_count}
