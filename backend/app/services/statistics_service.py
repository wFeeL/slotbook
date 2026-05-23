from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import BookingStatus
from app.db.models.booking import Booking
from app.db.models.service import Service
from app.db.models.staff import StaffMember
from app.schemas.statistics import (
    PERIOD_DAYS,
    DailyVolumeRow,
    StatisticsPeriod,
    StatisticsResponse,
    TopServiceRow,
    TopStaffRow,
)


class StatisticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def collect(
        self,
        business_id: int,
        period: StatisticsPeriod,
        staff_id: int | None = None,
        now: datetime | None = None,
    ) -> StatisticsResponse:
        cutoff = (now or datetime.now(UTC)) - timedelta(days=PERIOD_DAYS[period])

        base_filters = [Booking.business_id == business_id, Booking.starts_at >= cutoff]
        if staff_id is not None:
            base_filters.append(Booking.staff_id == staff_id)

        # Totals
        agg_stmt = select(
            func.count(Booking.id).label("total"),
            func.sum(
                case((Booking.status == BookingStatus.COMPLETED, 1), else_=0)
            ).label("completed"),
            func.sum(
                case((Booking.status == BookingStatus.NO_SHOW, 1), else_=0)
            ).label("no_show"),
            func.sum(
                case(
                    (
                        Booking.status.in_(
                            (
                                BookingStatus.CANCELLED_BY_CLIENT,
                                BookingStatus.CANCELLED_BY_ADMIN,
                            )
                        ),
                        1,
                    ),
                    else_=0,
                )
            ).label("cancelled"),
        ).where(*base_filters)
        agg = (await self.session.execute(agg_stmt)).one()
        total = int(agg.total or 0)
        completed = int(agg.completed or 0)
        no_show = int(agg.no_show or 0)
        cancelled = int(agg.cancelled or 0)

        # Revenue (completed only)
        revenue_stmt = (
            select(func.coalesce(func.sum(Service.price), 0))
            .select_from(Booking)
            .join(Service, Service.id == Booking.service_id)
            .where(*base_filters, Booking.status == BookingStatus.COMPLETED)
        )
        revenue = (await self.session.execute(revenue_stmt)).scalar_one() or Decimal("0")

        # Top services (completed)
        ts_stmt = (
            select(
                Service.id,
                Service.title,
                func.count(Booking.id),
                func.coalesce(func.sum(Service.price), 0),
            )
            .select_from(Booking)
            .join(Service, Service.id == Booking.service_id)
            .where(*base_filters, Booking.status == BookingStatus.COMPLETED)
            .group_by(Service.id, Service.title)
            .order_by(func.count(Booking.id).desc())
            .limit(5)
        )
        top_services = [
            TopServiceRow(
                service_id=sid,
                service_title=title,
                completed_count=int(cnt),
                revenue=Decimal(rev),
            )
            for sid, title, cnt, rev in (await self.session.execute(ts_stmt)).all()
        ]

        # Top staff
        st_stmt = (
            select(StaffMember.id, StaffMember.name, func.count(Booking.id))
            .select_from(Booking)
            .join(StaffMember, StaffMember.id == Booking.staff_id)
            .where(*base_filters, Booking.status == BookingStatus.COMPLETED)
            .group_by(StaffMember.id, StaffMember.name)
            .order_by(func.count(Booking.id).desc())
            .limit(5)
        )
        top_staff = [
            TopStaffRow(staff_id=sid, staff_name=name, completed_count=int(cnt))
            for sid, name, cnt in (await self.session.execute(st_stmt)).all()
        ]

        # Daily volume (group by day in UTC)
        day_stmt = (
            select(
                func.date(func.timezone("UTC", Booking.starts_at)).label("day"),
                func.count(Booking.id),
            )
            .where(*base_filters)
            .group_by("day")
            .order_by("day")
        )
        daily_volume = [
            DailyVolumeRow(date=day, bookings_count=int(cnt))
            for day, cnt in (await self.session.execute(day_stmt)).all()
        ]

        rate = (cancelled / total) if total else 0.0
        return StatisticsResponse(
            period=period,
            revenue=Decimal(revenue),
            total_bookings=total,
            completed_count=completed,
            no_show_count=no_show,
            cancellation_count=cancelled,
            cancellation_rate=round(rate, 3),
            top_services=top_services,
            top_staff=top_staff,
            daily_volume=daily_volume,
        )
