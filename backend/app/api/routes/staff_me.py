from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Query, Request, status
from sqlalchemy import select

from app.api.deps import CurrentUser, LinkedStaff, SessionDep
from app.core.errors import NotFound
from app.core.time import local_date_bounds_utc
from app.db.enums import BookingStatus, UserRole
from app.db.models.booking import Booking
from app.db.models.schedule import ScheduleException, WorkingHours
from app.db.models.service import Service
from app.db.models.user import User
from app.db.repositories.audit import AuditRepo
from app.db.repositories.bookings import BookingsRepo
from app.db.repositories.branches import BranchesRepo
from app.db.repositories.businesses import BusinessesRepo
from app.db.repositories.schedules import (
    ScheduleExceptionsRepo,
    WorkingHoursRepo,
)
from app.db.repositories.staff import StaffRepo
from app.schemas.bookings import BookingReschedule
from app.schemas.schedules import (
    ScheduleExceptionCreate,
    ScheduleExceptionRead,
    WorkingHoursEntry,
    WorkingHoursReplace,
)
from app.schemas.statistics import StatisticsPeriod, StatisticsResponse
from app.schemas.staff_me import (
    StaffBookingPatch,
    StaffBookingRead,
    StaffMeBranch,
    StaffMeResponse,
    StaffMeStaff,
    StaffScheduleBooking,
    StaffScheduleDay,
    StaffScheduleException,
    StaffScheduleInterval,
    StaffScheduleResponse,
)

router = APIRouter(prefix="/staff/me", tags=["staff-me"])


@router.get("", response_model=StaffMeResponse)
async def staff_me(user: CurrentUser, session: SessionDep) -> StaffMeResponse:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    staff = await StaffRepo(session).get_active_by_user_id(user.id)
    if staff is None:
        return StaffMeResponse(
            linked=False,
            staff=None,
            branch=None,
            business_timezone=business.timezone,
        )
    branch = await BranchesRepo(session).get(staff.branch_id)
    return StaffMeResponse(
        linked=True,
        staff=StaffMeStaff.model_validate(staff),
        branch=StaffMeBranch.model_validate(branch) if branch is not None else None,
        business_timezone=business.timezone,
    )


def _booking_to_read(
    booking: Booking,
    service: Service | None,
    client: User | None,
) -> StaffBookingRead:
    return StaffBookingRead(
        id=booking.id,
        starts_at=booking.starts_at,
        ends_at=booking.ends_at,
        status=booking.status,
        service_id=booking.service_id,
        service_title=service.title if service else "",
        service_duration_minutes=service.duration_minutes if service else 0,
        service_price=str(service.price) if service and service.price is not None else None,
        client_first_name=client.first_name if client else None,
        client_last_name=client.last_name if client else None,
        client_phone=client.phone if client else None,
        client_username=client.username if client else None,
        client_comment=booking.client_comment,
        admin_comment=booking.admin_comment,
    )


@router.get("/bookings", response_model=list[StaffBookingRead])
async def list_my_bookings(
    staff: LinkedStaff,
    session: SessionDep,
    date_filter: Annotated[date | None, Query(alias="date")] = None,
    date_from: Annotated[date | None, Query(alias="from")] = None,
    date_to: Annotated[date | None, Query(alias="to")] = None,
    status_filter: Annotated[BookingStatus | None, Query(alias="status")] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[StaffBookingRead]:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None

    stmt = select(Booking).where(Booking.staff_id == staff.id)
    if date_filter is not None:
        s, e = local_date_bounds_utc(date_filter, business.timezone)
        stmt = stmt.where(Booking.starts_at >= s, Booking.starts_at < e)
    else:
        if date_from is not None:
            s, _ = local_date_bounds_utc(date_from, business.timezone)
            stmt = stmt.where(Booking.starts_at >= s)
        if date_to is not None:
            _, e = local_date_bounds_utc(date_to, business.timezone)
            stmt = stmt.where(Booking.starts_at < e)
    if status_filter is not None:
        stmt = stmt.where(Booking.status == status_filter)
    stmt = stmt.order_by(Booking.starts_at).limit(limit).offset(offset)
    bookings = list((await session.execute(stmt)).scalars().all())

    if not bookings:
        return []

    svc_ids = {b.service_id for b in bookings}
    cli_ids = {b.client_id for b in bookings}
    services_map: dict[int, Service] = {
        s.id: s
        for s in (await session.execute(
            select(Service).where(Service.id.in_(svc_ids))
        )).scalars().all()
    }
    clients_map: dict[int, User] = {
        u.id: u
        for u in (await session.execute(
            select(User).where(User.id.in_(cli_ids))
        )).scalars().all()
    }
    return [
        _booking_to_read(b, services_map.get(b.service_id), clients_map.get(b.client_id))
        for b in bookings
    ]


@router.patch("/bookings/{booking_id}", response_model=StaffBookingRead)
async def patch_my_booking(
    booking_id: int,
    body: StaffBookingPatch,
    staff: LinkedStaff,
    session: SessionDep,
) -> StaffBookingRead:
    booking = await BookingsRepo(session).get(booking_id)
    if booking is None or booking.staff_id != staff.id:
        raise NotFound("Запись не найдена")

    previous_status = booking.status.value
    if body.status is not None:
        allowed = {BookingStatus.COMPLETED, BookingStatus.NO_SHOW}
        if body.status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Status not allowed for staff; use admin endpoint to cancel",
            )
        booking.status = body.status
        AuditRepo(session).log(
            actor_user_id=staff.user_id or 0,
            action=f"booking_status_{body.status.value}",
            entity_type="booking",
            entity_id=booking.id,
            metadata={"previous_status": previous_status, "actor_role": "staff"},
        )
    if body.admin_comment is not None:
        booking.admin_comment = body.admin_comment

    await session.commit()
    await session.refresh(booking)

    svc = await session.get(Service, booking.service_id)
    cli = await session.get(User, booking.client_id)
    return _booking_to_read(booking, svc, cli)


@router.get("/schedule", response_model=StaffScheduleResponse)
async def my_schedule(
    staff: LinkedStaff,
    session: SessionDep,
    week_start: Annotated[date | None, Query()] = None,
) -> StaffScheduleResponse:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    tz = ZoneInfo(business.timezone)

    if week_start is None:
        today_local = datetime.now(UTC).astimezone(tz).date()
        week_start = today_local - timedelta(days=today_local.weekday())
    week_end = week_start + timedelta(days=7)

    wh_rows = await WorkingHoursRepo(session).list_for_staff(staff.id)
    wh_by_day: dict[int, list] = {i: [] for i in range(7)}
    for r in wh_rows:
        if r.is_active:
            wh_by_day[r.weekday].append(r)

    exceptions_all = await ScheduleExceptionsRepo(session).list_for_staff_range(
        staff.id, week_start, week_end
    )
    exc_by_date: dict[date, list] = {}
    for e in exceptions_all:
        exc_by_date.setdefault(e.date, []).append(e)

    week_start_utc, _ = local_date_bounds_utc(week_start, business.timezone)
    _, week_end_utc = local_date_bounds_utc(week_end - timedelta(days=1), business.timezone)
    bookings = await BookingsRepo(session).list_active_for_staff_range(
        staff.id, week_start_utc, week_end_utc
    )
    svc_ids = {b.service_id for b in bookings}
    cli_ids = {b.client_id for b in bookings}
    services = (
        {
            s.id: s
            for s in (await session.execute(
                select(Service).where(Service.id.in_(svc_ids))
            )).scalars().all()
        }
        if svc_ids
        else {}
    )
    clients = (
        {
            u.id: u
            for u in (await session.execute(
                select(User).where(User.id.in_(cli_ids))
            )).scalars().all()
        }
        if cli_ids
        else {}
    )

    bookings_by_local_date: dict[date, list] = {}
    for b in bookings:
        local_d = b.starts_at.astimezone(tz).date()
        bookings_by_local_date.setdefault(local_d, []).append(b)

    days: list[StaffScheduleDay] = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        weekday = d.weekday()
        intervals = [
            StaffScheduleInterval(start_time=r.start_time, end_time=r.end_time)
            for r in wh_by_day.get(weekday, [])
        ]
        day_excs = [
            StaffScheduleException(
                id=e.id,
                date=e.date,
                type=e.type,
                start_time=e.start_time,
                end_time=e.end_time,
                reason=e.reason,
            )
            for e in exc_by_date.get(d, [])
        ]
        day_bookings = [
            StaffScheduleBooking(
                id=b.id,
                starts_at=b.starts_at,
                ends_at=b.ends_at,
                service_title=(services.get(b.service_id).title if services.get(b.service_id) else ""),
                client_first_name=(
                    clients.get(b.client_id).first_name if clients.get(b.client_id) else None
                ),
                status=b.status,
            )
            for b in bookings_by_local_date.get(d, [])
        ]
        days.append(
            StaffScheduleDay(
                date=d,
                weekday=weekday,
                working_intervals=intervals,
                exceptions=day_excs,
                bookings=day_bookings,
            )
        )

    return StaffScheduleResponse(
        week_start=week_start,
        business_timezone=business.timezone,
        days=days,
    )


# ---------------------------------------------------------------------------
# Staff manages own working hours and schedule exceptions
# ---------------------------------------------------------------------------


@router.get("/working-hours", response_model=list[WorkingHoursEntry])
async def my_working_hours(
    staff: LinkedStaff, session: SessionDep
) -> list[WorkingHoursEntry]:
    rows = await WorkingHoursRepo(session).list_for_staff(staff.id)
    return [WorkingHoursEntry.model_validate(r) for r in rows]


@router.put("/working-hours", status_code=status.HTTP_204_NO_CONTENT)
async def replace_my_working_hours(
    body: WorkingHoursReplace, staff: LinkedStaff, session: SessionDep
) -> None:
    entries = [
        WorkingHours(
            staff_id=staff.id,
            weekday=e.weekday,
            start_time=e.start_time,
            end_time=e.end_time,
            is_active=e.is_active,
        )
        for e in body.entries
    ]
    await WorkingHoursRepo(session).replace_for_staff(staff.id, entries)
    await session.commit()


@router.post(
    "/exceptions",
    response_model=ScheduleExceptionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_my_exception(
    body: ScheduleExceptionCreate,
    staff: LinkedStaff,
    session: SessionDep,
) -> ScheduleExceptionRead:
    exc = ScheduleException(
        staff_id=staff.id,
        date=body.date,
        type=body.type,
        start_time=body.start_time,
        end_time=body.end_time,
        reason=body.reason,
    )
    ScheduleExceptionsRepo(session).add(exc)
    await session.commit()
    await session.refresh(exc)
    return ScheduleExceptionRead.model_validate(exc)


@router.delete(
    "/exceptions/{exception_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_my_exception(
    exception_id: int, staff: LinkedStaff, session: SessionDep
) -> None:
    # Verify exception belongs to this staff before deleting.
    from sqlalchemy import select as _select
    exc = (
        await session.execute(
            _select(ScheduleException).where(ScheduleException.id == exception_id)
        )
    ).scalar_one_or_none()
    if exc is None or exc.staff_id != staff.id:
        raise NotFound("Исключение не найдено")
    deleted = await ScheduleExceptionsRepo(session).delete(exception_id)
    if not deleted:
        raise NotFound("Исключение не найдено")
    await session.commit()


# ---------------------------------------------------------------------------
# Staff cancels / reschedules own booking (writes notifications via service)
# ---------------------------------------------------------------------------


async def _ensure_own_booking(session, staff, booking_id: int):
    """Return booking if it belongs to this staff; raise NotFound otherwise."""
    from app.db.repositories.bookings import BookingsRepo as _BR
    bk = await _BR(session).get(booking_id)
    if bk is None or bk.staff_id != staff.id:
        raise NotFound("Запись не найдена")
    return bk


@router.post("/bookings/{booking_id}/cancel", response_model=StaffBookingRead)
async def cancel_my_booking(
    booking_id: int,
    staff: LinkedStaff,
    user: CurrentUser,
    session: SessionDep,
    request: Request,
) -> StaffBookingRead:
    from app.services.booking_service import BookingService
    from app.services.notification_service import NotificationService

    await _ensure_own_booking(session, staff, booking_id)
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None

    booking = await BookingService(session).cancel_booking(
        business=business,
        actor_user_id=user.id,
        actor_role=UserRole.STAFF,
        booking_id=booking_id,
    )
    try:
        await NotificationService(session, request.app.state.bot).dispatch_pending_for_booking(
            booking.id
        )
    except Exception:
        pass

    svc = await session.get(Service, booking.service_id)
    cli = await session.get(User, booking.client_id)
    return _booking_to_read(booking, svc, cli)


@router.post("/bookings/{booking_id}/reschedule", response_model=StaffBookingRead)
async def reschedule_my_booking(
    booking_id: int,
    body: BookingReschedule,
    staff: LinkedStaff,
    user: CurrentUser,
    session: SessionDep,
    request: Request,
) -> StaffBookingRead:
    from app.services.booking_service import BookingService
    from app.services.notification_service import NotificationService

    await _ensure_own_booking(session, staff, booking_id)
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None

    booking = await BookingService(session).reschedule_booking(
        business=business,
        actor_user_id=user.id,
        actor_role=UserRole.STAFF,
        booking_id=booking_id,
        new_starts_at=body.starts_at,
    )
    try:
        await NotificationService(session, request.app.state.bot).dispatch_pending_for_booking(
            booking.id
        )
    except Exception:
        pass

    svc = await session.get(Service, booking.service_id)
    cli = await session.get(User, booking.client_id)
    return _booking_to_read(booking, svc, cli)


@router.get("/statistics", response_model=StatisticsResponse)
async def my_statistics(
    staff: LinkedStaff,
    session: SessionDep,
    period: StatisticsPeriod = StatisticsPeriod.LAST_30D,
) -> StatisticsResponse:
    from app.services.statistics_service import StatisticsService
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    return await StatisticsService(session).collect(business.id, period, staff_id=staff.id)
