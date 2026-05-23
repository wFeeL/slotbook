from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Annotated

import structlog
from fastapi import APIRouter, Query, Request, Response, status
from sqlalchemy import select

from app.api.deps import AdminUser, SessionDep
from app.core.config import Settings, get_settings
from app.core.errors import CannotCancelInCurrentStatus, NotFound
from app.core.time import local_date_bounds_utc
from app.db.enums import BookingSource, BookingStatus, UserRole
from app.db.models.branch import Branch
from app.db.models.schedule import ScheduleException, WorkingHours
from app.db.models.service import Service
from app.db.models.staff import StaffMember
from app.db.models.user import User
from app.db.repositories.admin_invites import AdminInvitesRepo
from app.db.repositories.audit import AuditRepo
from app.db.repositories.bookings import BookingsRepo
from app.db.repositories.branches import BranchesRepo
from app.db.repositories.businesses import BusinessesRepo
from app.db.repositories.schedules import ScheduleExceptionsRepo, WorkingHoursRepo
from app.db.repositories.services import ServicesRepo
from app.db.repositories.staff import StaffRepo
from app.db.repositories.users import UsersRepo
from app.schemas.admin import (
    AdminBookingCreate,
    AdminBookingPatch,
    AdminBookingRead,
    BusinessRead,
    BusinessUpdate,
    DashboardCounts,
    DashboardResponse,
)
from app.schemas.bookings import BookingReschedule
from app.schemas.branches import BranchCreate, BranchRead, BranchUpdate
from app.schemas.schedules import (
    ScheduleExceptionCreate,
    ScheduleExceptionRead,
    WorkingHoursEntry,
    WorkingHoursReplace,
)
from app.schemas.services import ServiceCreate, ServiceRead, ServiceUpdate
from app.schemas.staff import (
    StaffCreate,
    StaffRead,
    StaffReadWithServices,
    StaffServicesUpdate,
    StaffUpdate,
)
from app.schemas.statistics import StatisticsPeriod, StatisticsResponse
from app.schemas.team import (
    AdminInviteCreate,
    AdminInviteRead,
    TeamMember,
    TeamResponse,
)
from app.services import export_service
from app.services.booking_service import BookingService
from app.services.notification_service import NotificationService
from app.services.statistics_service import StatisticsService

log = structlog.get_logger()

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/services", response_model=ServiceRead, status_code=status.HTTP_201_CREATED)
async def create_service(
    body: ServiceCreate, _admin: AdminUser, session: SessionDep
) -> ServiceRead:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    branch_id = getattr(body, "branch_id", None)
    if branch_id is None:
        default_branch = await BranchesRepo(session).get_default(business.id)
        if default_branch is None:
            raise NotFound("No active branch found; create one first")
        branch_id = default_branch.id
    else:
        branch = await BranchesRepo(session).get(branch_id)
        if branch is None or branch.business_id != business.id:
            raise NotFound("Branch not found")
    service = Service(
        business_id=business.id,
        branch_id=branch_id,
        title=body.title,
        description=body.description,
        duration_minutes=body.duration_minutes,
        price=body.price,
        sort_order=body.sort_order,
    )
    ServicesRepo(session).add(service)
    await session.commit()
    await session.refresh(service)
    return ServiceRead.model_validate(service)


@router.patch("/services/{service_id}", response_model=ServiceRead)
async def update_service(
    service_id: int, body: ServiceUpdate, _admin: AdminUser, session: SessionDep
) -> ServiceRead:
    repo = ServicesRepo(session)
    service = await repo.get(service_id)
    if service is None:
        raise NotFound("Service not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(service, field, value)
    await session.commit()
    await session.refresh(service)
    return ServiceRead.model_validate(service)


@router.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(service_id: int, _admin: AdminUser, session: SessionDep) -> None:
    repo = ServicesRepo(session)
    service = await repo.get(service_id)
    if service is None:
        raise NotFound("Service not found")
    await repo.soft_delete(service)
    await session.commit()


@router.get("/staff", response_model=list[StaffReadWithServices])
async def admin_list_staff(
    _admin: AdminUser,
    session: SessionDep,
    include_archived: bool = True,
) -> list[StaffReadWithServices]:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    repo = StaffRepo(session)
    staff = await repo.list_for_business(business.id, include_archived=include_archived)
    out: list[StaffReadWithServices] = []
    for s in staff:
        sids = await repo.list_service_ids(s.id)
        out.append(
            StaffReadWithServices(
                id=s.id,
                branch_id=s.branch_id,
                name=s.name,
                description=s.description,
                is_active=s.is_active,
                service_ids=sids,
            )
        )
    return out


@router.post("/staff", response_model=StaffRead, status_code=status.HTTP_201_CREATED)
async def create_staff(body: StaffCreate, _admin: AdminUser, session: SessionDep) -> StaffRead:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    branch_id = getattr(body, "branch_id", None)
    if branch_id is None:
        default_branch = await BranchesRepo(session).get_default(business.id)
        if default_branch is None:
            raise NotFound("No active branch found; create one first")
        branch_id = default_branch.id
    else:
        branch = await BranchesRepo(session).get(branch_id)
        if branch is None or branch.business_id != business.id:
            raise NotFound("Branch not found")
    staff = StaffMember(
        business_id=business.id,
        branch_id=branch_id,
        name=body.name,
        description=body.description,
    )
    StaffRepo(session).add(staff)
    await session.commit()
    await session.refresh(staff)
    return StaffRead.model_validate(staff)


@router.patch("/staff/{staff_id}", response_model=StaffRead)
async def update_staff(
    staff_id: int, body: StaffUpdate, _admin: AdminUser, session: SessionDep
) -> StaffRead:
    repo = StaffRepo(session)
    staff = await repo.get(staff_id)
    if staff is None:
        raise NotFound("Staff member not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(staff, field, value)
    await session.commit()
    await session.refresh(staff)
    return StaffRead.model_validate(staff)


@router.delete("/staff/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_staff(staff_id: int, _admin: AdminUser, session: SessionDep) -> None:
    repo = StaffRepo(session)
    staff = await repo.get(staff_id)
    if staff is None:
        raise NotFound("Staff member not found")
    staff.is_active = False
    await session.commit()


@router.put("/staff/{staff_id}/services", status_code=status.HTTP_204_NO_CONTENT)
async def replace_staff_services(
    staff_id: int, body: StaffServicesUpdate, _admin: AdminUser, session: SessionDep
) -> None:
    repo = StaffRepo(session)
    staff = await repo.get(staff_id)
    if staff is None:
        raise NotFound("Staff member not found")
    await repo.replace_services(staff_id, body.service_ids)
    await session.commit()


@router.get("/staff/{staff_id}/working-hours", response_model=list[WorkingHoursEntry])
async def get_working_hours(
    staff_id: int, _admin: AdminUser, session: SessionDep
) -> list[WorkingHoursEntry]:
    if (await StaffRepo(session).get(staff_id)) is None:
        raise NotFound("Staff member not found")
    rows = await WorkingHoursRepo(session).list_for_staff(staff_id)
    return [WorkingHoursEntry.model_validate(r) for r in rows]


@router.put("/staff/{staff_id}/working-hours", status_code=status.HTTP_204_NO_CONTENT)
async def put_working_hours(
    staff_id: int, body: WorkingHoursReplace, _admin: AdminUser, session: SessionDep
) -> None:
    if (await StaffRepo(session).get(staff_id)) is None:
        raise NotFound("Staff member not found")
    entries = [
        WorkingHours(
            staff_id=staff_id,
            weekday=e.weekday,
            start_time=e.start_time,
            end_time=e.end_time,
            is_active=e.is_active,
        )
        for e in body.entries
    ]
    await WorkingHoursRepo(session).replace_for_staff(staff_id, entries)
    await session.commit()


@router.post(
    "/staff/{staff_id}/exceptions",
    response_model=ScheduleExceptionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_exception(
    staff_id: int, body: ScheduleExceptionCreate, _admin: AdminUser, session: SessionDep
) -> ScheduleExceptionRead:
    if (await StaffRepo(session).get(staff_id)) is None:
        raise NotFound("Staff member not found")
    exception = ScheduleException(
        staff_id=staff_id,
        date=body.date,
        type=body.type,
        start_time=body.start_time,
        end_time=body.end_time,
        reason=body.reason,
    )
    ScheduleExceptionsRepo(session).add(exception)
    await session.commit()
    await session.refresh(exception)
    return ScheduleExceptionRead.model_validate(exception)


@router.delete(
    "/staff/{staff_id}/exceptions/{exception_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_exception(
    staff_id: int, exception_id: int, _admin: AdminUser, session: SessionDep
) -> None:
    if (await StaffRepo(session).get(staff_id)) is None:
        raise NotFound("Staff member not found")
    deleted = await ScheduleExceptionsRepo(session).delete(exception_id)
    if not deleted:
        raise NotFound("Exception not found")
    await session.commit()


# ---------------------------------------------------------------------------
# Admin booking endpoints
# ---------------------------------------------------------------------------


async def _enrich_bookings(
    session: "SessionDep", bookings: list
) -> list[AdminBookingRead]:
    """Batch-load related service/staff/user rows and produce AdminBookingRead with names."""
    if not bookings:
        return []
    service_ids = {b.service_id for b in bookings}
    staff_ids = {b.staff_id for b in bookings}
    user_ids = {b.client_id for b in bookings}

    services_map: dict[int, Service] = {
        s.id: s
        for s in (
            await session.execute(select(Service).where(Service.id.in_(service_ids)))
        ).scalars().all()
    }
    staff_map: dict[int, StaffMember] = {
        s.id: s
        for s in (
            await session.execute(select(StaffMember).where(StaffMember.id.in_(staff_ids)))
        ).scalars().all()
    }
    users_map: dict[int, User] = {
        u.id: u
        for u in (
            await session.execute(select(User).where(User.id.in_(user_ids)))
        ).scalars().all()
    }

    out: list[AdminBookingRead] = []
    for b in bookings:
        svc = services_map.get(b.service_id)
        stf = staff_map.get(b.staff_id)
        usr = users_map.get(b.client_id)
        out.append(
            AdminBookingRead(
                id=b.id,
                branch_id=b.branch_id,
                client_id=b.client_id,
                service_id=b.service_id,
                staff_id=b.staff_id,
                starts_at=b.starts_at,
                ends_at=b.ends_at,
                status=b.status,
                client_comment=b.client_comment,
                admin_comment=b.admin_comment,
                service_title=svc.title if svc else None,
                staff_name=stf.name if stf else None,
                client_first_name=usr.first_name if usr else None,
                client_last_name=usr.last_name if usr else None,
                client_telegram_id=usr.telegram_id if usr else None,
            )
        )
    return out


async def _enrich_booking(session: "SessionDep", booking) -> AdminBookingRead:
    rows = await _enrich_bookings(session, [booking])
    return rows[0]


@router.get("/bookings", response_model=list[AdminBookingRead])
async def admin_list_bookings(
    admin: AdminUser,
    session: SessionDep,
    date_filter: Annotated[date | None, Query(alias="date")] = None,
    week_start: Annotated[date | None, Query(alias="week_start")] = None,
    staff_id: int | None = None,
    service_id: int | None = None,
    status_filter: Annotated[BookingStatus | None, Query(alias="status")] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[AdminBookingRead]:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    repo = BookingsRepo(session)
    if week_start is not None:
        week_start_utc, _ = local_date_bounds_utc(week_start, business.timezone)
        end_of_week = week_start + timedelta(days=7)
        _, week_end_utc = local_date_bounds_utc(
            end_of_week - timedelta(days=1), business.timezone
        )
        bookings = await repo.list_admin_for_local_week(
            business.id,
            week_start_utc,
            week_end_utc,
            staff_id=staff_id,
            service_id=service_id,
            status=status_filter,
            limit=limit,
            offset=offset,
        )
    elif date_filter is not None:
        start_utc, end_utc = local_date_bounds_utc(date_filter, business.timezone)
        bookings = await repo.list_admin_for_local_date(
            business.id,
            start_utc,
            end_utc,
            staff_id=staff_id,
            service_id=service_id,
            status=status_filter,
            limit=limit,
            offset=offset,
        )
    else:
        bookings = await repo.list_admin(
            business.id,
            staff_id=staff_id,
            service_id=service_id,
            status=status_filter,
            limit=limit,
            offset=offset,
        )
    return await _enrich_bookings(session, bookings)


@router.patch("/bookings/{booking_id}", response_model=AdminBookingRead)
async def admin_patch_booking(
    booking_id: int,
    body: AdminBookingPatch,
    admin: AdminUser,
    session: SessionDep,
) -> AdminBookingRead:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    repo = BookingsRepo(session)
    booking = await repo.get(booking_id)
    if booking is None or booking.business_id != business.id:
        raise NotFound("Booking not found")

    if body.admin_comment is not None:
        booking.admin_comment = body.admin_comment

    previous_status = booking.status.value
    if body.status is not None:
        allowed = {BookingStatus.COMPLETED, BookingStatus.NO_SHOW}
        if body.status not in allowed:
            raise CannotCancelInCurrentStatus("Use the dedicated cancel endpoint for cancellation")
        booking.status = body.status
        AuditRepo(session).log(
            actor_user_id=admin.id,
            action=f"booking_status_{body.status.value}",
            entity_type="booking",
            entity_id=booking.id,
            metadata={"previous_status": previous_status},
        )

    await session.commit()
    await session.refresh(booking)
    return await _enrich_booking(session, booking)


@router.post("/bookings", response_model=AdminBookingRead, status_code=status.HTTP_201_CREATED)
async def admin_create_booking(
    body: AdminBookingCreate,
    admin: AdminUser,
    session: SessionDep,
    request: Request,
) -> AdminBookingRead:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None

    # Upsert client by telegram_id
    users_repo = UsersRepo(session)
    client = await users_repo.get_by_telegram_id(body.client_telegram_id)
    if client is None:
        client = User(
            telegram_id=body.client_telegram_id,
            role=UserRole.CLIENT,
        )
        session.add(client)
        await session.flush()

    booking = await BookingService(session).create_booking(
        business=business,
        actor_user_id=admin.id,
        client_id=client.id,
        staff_id=body.staff_id,
        service_id=body.service_id,
        starts_at=body.starts_at,
        client_comment=body.client_comment,
        source=BookingSource.ADMIN_MANUAL,
    )

    if body.admin_comment is not None:
        booking.admin_comment = body.admin_comment
        await session.commit()
        await session.refresh(booking)

    try:
        await NotificationService(session, request.app.state.bot).dispatch_pending_for_booking(
            booking.id
        )
    except Exception:
        log.exception("notification.dispatch_failed_in_route", booking_id=booking.id)
    return await _enrich_booking(session, booking)


@router.post("/bookings/{booking_id}/cancel", response_model=AdminBookingRead)
async def admin_cancel_booking(
    booking_id: int,
    admin: AdminUser,
    session: SessionDep,
    request: Request,
) -> AdminBookingRead:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    booking = await BookingService(session).cancel_booking(
        business=business,
        actor_user_id=admin.id,
        actor_role=admin.role,
        booking_id=booking_id,
    )
    try:
        await NotificationService(session, request.app.state.bot).dispatch_pending_for_booking(
            booking.id
        )
    except Exception:
        log.exception("notification.dispatch_failed_in_route", booking_id=booking.id)
    return await _enrich_booking(session, booking)


@router.post("/bookings/{booking_id}/reschedule", response_model=AdminBookingRead)
async def admin_reschedule_booking(
    booking_id: int,
    body: BookingReschedule,
    admin: AdminUser,
    session: SessionDep,
    request: Request,
) -> AdminBookingRead:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    booking = await BookingService(session).reschedule_booking(
        business=business,
        actor_user_id=admin.id,
        actor_role=admin.role,
        booking_id=booking_id,
        new_starts_at=body.starts_at,
    )
    try:
        await NotificationService(session, request.app.state.bot).dispatch_pending_for_booking(
            booking.id
        )
    except Exception:
        log.exception("notification.dispatch_failed_in_route", booking_id=booking.id)
    return await _enrich_booking(session, booking)


@router.get("/dashboard", response_model=DashboardResponse)
async def admin_dashboard(
    admin: AdminUser,
    session: SessionDep,
) -> DashboardResponse:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None

    from zoneinfo import ZoneInfo

    now_utc = datetime.now(UTC)
    tz = ZoneInfo(business.timezone)
    today_local = now_utc.astimezone(tz).date()

    today_utc_start, today_utc_end = local_date_bounds_utc(today_local, business.timezone)

    week_start_local = today_local - timedelta(days=today_local.weekday())
    week_utc_start, _ = local_date_bounds_utc(week_start_local, business.timezone)
    week_end_local = week_start_local + timedelta(days=7)
    _, week_utc_end = local_date_bounds_utc(week_end_local - timedelta(days=1), business.timezone)

    no_show_window_start = now_utc - timedelta(days=30)

    counts = await BookingsRepo(session).dashboard_counts(
        business.id,
        today_utc_start=today_utc_start,
        today_utc_end=today_utc_end,
        week_utc_start=week_utc_start,
        week_utc_end=week_utc_end,
        no_show_window_start=no_show_window_start,
    )
    return DashboardResponse(counts=DashboardCounts(**counts))


@router.get("/business", response_model=BusinessRead)
async def admin_get_business(_admin: AdminUser, session: SessionDep) -> BusinessRead:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    return BusinessRead.model_validate(business)


@router.patch("/business", response_model=BusinessRead)
async def admin_patch_business(
    body: BusinessUpdate, _admin: AdminUser, session: SessionDep
) -> BusinessRead:
    repo = BusinessesRepo(session)
    business = await repo.get_singleton()
    assert business is not None
    updates = body.model_dump(exclude_unset=True)
    await repo.update(business, **updates)
    await session.commit()
    return BusinessRead.model_validate(business)


@router.get("/statistics", response_model=StatisticsResponse)
async def admin_statistics(
    _admin: AdminUser,
    session: SessionDep,
    period: StatisticsPeriod = StatisticsPeriod.LAST_30D,
    staff_id: int | None = None,
) -> StatisticsResponse:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    return await StatisticsService(session).collect(business.id, period, staff_id=staff_id)


@router.get("/exports/bookings.csv")
async def export_bookings_csv(
    _admin: AdminUser,
    session: SessionDep,
    date_from: Annotated[date | None, Query(alias="from")] = None,
    date_to: Annotated[date | None, Query(alias="to")] = None,
    staff_id: int | None = None,
) -> Response:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    body = await export_service.to_csv(session, business.id, date_from, date_to, staff_id)
    filename = f"slotbook-bookings-{datetime.now(UTC).strftime('%Y%m%d')}.csv"
    return Response(
        content=body,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/exports/bookings.xlsx")
async def export_bookings_xlsx(
    _admin: AdminUser,
    session: SessionDep,
    date_from: Annotated[date | None, Query(alias="from")] = None,
    date_to: Annotated[date | None, Query(alias="to")] = None,
    staff_id: int | None = None,
) -> Response:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    body = await export_service.to_xlsx(session, business.id, date_from, date_to, staff_id)
    filename = f"slotbook-bookings-{datetime.now(UTC).strftime('%Y%m%d')}.xlsx"
    return Response(
        content=body,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Admin team / invites
# ---------------------------------------------------------------------------


def _invite_url(token: str, settings: Settings) -> str:
    if not settings.BOT_USERNAME:
        return f"https://t.me/your_bot?start=invite_{token}"
    return f"https://t.me/{settings.BOT_USERNAME}?start=invite_{token}"


@router.get("/team", response_model=TeamResponse)
async def admin_team(_admin: AdminUser, session: SessionDep) -> TeamResponse:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    stmt = (
        select(User)
        .where(User.role.in_([UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.STAFF]))
        .order_by(User.created_at.desc())
    )
    members = [
        TeamMember.model_validate(u) for u in (await session.execute(stmt)).scalars().all()
    ]
    invites_raw = await AdminInvitesRepo(session).list_active(business.id)
    settings = get_settings()
    invites = [
        AdminInviteRead(
            id=i.id,
            token=i.token,
            role=i.role,
            created_at=i.created_at,
            expires_at=i.expires_at,
            url=_invite_url(i.token, settings),
        )
        for i in invites_raw
    ]
    return TeamResponse(members=members, invites=invites)


@router.post("/invites", response_model=AdminInviteRead, status_code=status.HTTP_201_CREATED)
async def admin_create_invite(
    body: AdminInviteCreate, admin: AdminUser, session: SessionDep
) -> AdminInviteRead:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    invite = await AdminInvitesRepo(session).create(
        business_id=business.id,
        role=UserRole(body.role),
        created_by_user_id=admin.id,
        ttl_hours=body.ttl_hours,
    )
    await session.commit()
    settings = get_settings()
    return AdminInviteRead(
        id=invite.id,
        token=invite.token,
        role=invite.role,
        created_at=invite.created_at,
        expires_at=invite.expires_at,
        url=_invite_url(invite.token, settings),
    )


@router.delete("/invites/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_revoke_invite(
    invite_id: int, _admin: AdminUser, session: SessionDep
) -> None:
    ok = await AdminInvitesRepo(session).revoke(invite_id)
    if not ok:
        raise NotFound("Invite not found or already used")
    await session.commit()


# ---------------------------------------------------------------------------
# Admin branches endpoints
# ---------------------------------------------------------------------------


@router.get("/branches", response_model=list[BranchRead])
async def admin_list_branches(_admin: AdminUser, session: SessionDep) -> list[BranchRead]:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    branches = await BranchesRepo(session).list_for_business(business.id, include_archived=True)
    return [BranchRead.model_validate(b) for b in branches]


@router.post("/branches", response_model=BranchRead, status_code=status.HTTP_201_CREATED)
async def admin_create_branch(
    body: BranchCreate, _admin: AdminUser, session: SessionDep
) -> BranchRead:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    branch = Branch(
        business_id=business.id,
        name=body.name,
        address=body.address,
        timezone=body.timezone,
        sort_order=body.sort_order,
    )
    BranchesRepo(session).add(branch)
    await session.commit()
    await session.refresh(branch)
    return BranchRead.model_validate(branch)


@router.patch("/branches/{branch_id}", response_model=BranchRead)
async def admin_update_branch(
    branch_id: int, body: BranchUpdate, _admin: AdminUser, session: SessionDep
) -> BranchRead:
    branch = await BranchesRepo(session).get(branch_id)
    if branch is None:
        raise NotFound("Branch not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(branch, k, v)
    await session.commit()
    await session.refresh(branch)
    return BranchRead.model_validate(branch)


@router.delete("/branches/{branch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_archive_branch(
    branch_id: int, _admin: AdminUser, session: SessionDep
) -> None:
    branch = await BranchesRepo(session).get(branch_id)
    if branch is None:
        raise NotFound("Branch not found")
    branch.is_active = False
    await session.commit()
