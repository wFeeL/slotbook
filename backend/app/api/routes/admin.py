from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy import select

from app.api.deps import AdminUser, SessionDep
from app.core.config import Settings, get_settings
from app.core.errors import CannotCancelInCurrentStatus, NotFound
from app.core.time import local_date_bounds_utc
from app.db.enums import BookingSource, BookingStatus, PhotoOwnerType, UserRole
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
from app.db.repositories.pending_photo_uploads import PendingPhotoUploadsRepo
from app.db.repositories.photos import PhotosRepo
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
from app.schemas.photos import (
    PhotoSortUpdate,
    PhotoUploadIntentCreate,
    PhotoUploadIntentResponse,
)
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
    TeamMemberRoleUpdate,
    TeamResponse,
)
from app.schemas.users import UserBrief
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
    from fastapi import HTTPException
    from sqlalchemy.exc import IntegrityError

    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    branch_id = body.branch_id
    if branch_id is None:
        default_branch = await BranchesRepo(session).get_default(business.id)
        if default_branch is None:
            raise NotFound("No active branch found; create one first")
        branch_id = default_branch.id
    else:
        branch = await BranchesRepo(session).get(branch_id)
        if branch is None or branch.business_id != business.id:
            raise NotFound("Branch not found")

    if body.user_id is not None:
        target = await UsersRepo(session).get_by_id(body.user_id)
        if target is None:
            raise NotFound("User not found")
        if target.role not in {UserRole.STAFF, UserRole.ADMIN, UserRole.SUPERADMIN}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="User role must be staff/admin/superadmin",
            )

    staff = StaffMember(
        business_id=business.id,
        branch_id=branch_id,
        user_id=body.user_id,
        name=body.name,
        description=body.description,
    )
    StaffRepo(session).add(staff)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        if "ux_staff_user_active" in str(exc.orig or exc):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Этот пользователь уже привязан к другому мастеру",
            ) from exc
        raise
    await session.refresh(staff)
    return StaffRead.model_validate(staff)


@router.patch("/staff/{staff_id}", response_model=StaffRead)
async def update_staff(
    staff_id: int, body: StaffUpdate, _admin: AdminUser, session: SessionDep
) -> StaffRead:
    from fastapi import HTTPException
    from sqlalchemy.exc import IntegrityError

    repo = StaffRepo(session)
    staff = await repo.get(staff_id)
    if staff is None:
        raise NotFound("Staff member not found")

    updates = body.model_dump(exclude_unset=True)

    if "user_id" in updates and updates["user_id"] is not None:
        target = await UsersRepo(session).get_by_id(updates["user_id"])
        if target is None:
            raise NotFound("User not found")
        if target.role not in {UserRole.STAFF, UserRole.ADMIN, UserRole.SUPERADMIN}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="User role must be staff/admin/superadmin",
            )

    for field, value in updates.items():
        setattr(staff, field, value)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        if "ux_staff_user_active" in str(exc.orig or exc):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Этот пользователь уже привязан к другому мастеру",
            ) from exc
        raise
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
    session: SessionDep, bookings: list
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
                client_username=usr.username if usr else None,
                client_phone=usr.phone if usr else None,
            )
        )
    return out


async def _enrich_booking(session: SessionDep, booking) -> AdminBookingRead:
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
    await _enqueue_review_request(session, booking=booking, previous_status=previous_status)
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


from fastapi import Header  # noqa: E402


async def _resolve_admin_for_export(
    session: SessionDep,
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    ticket: Annotated[str | None, Query()] = None,
) -> User:
    """Resolve current admin for file-download endpoints.

    Two paths:
    - `Authorization: Bearer <jwt>` — normal full-scope admin JWT.
    - `?ticket=<jwt>` — short-lived (default 60s) download-scoped token issued
      via POST /admin/exports/ticket. The token's purpose+kind+params claims
      are bound to the URL the user just clicked, so leaking the URL via logs
      or Referer headers cannot be replayed against any other endpoint.
    """
    from app.core.config import get_settings
    from app.core.errors import Forbidden as _Forbidden
    from app.core.errors import InvalidToken as _InvalidToken
    from app.core.security import decode_jwt
    from app.db.repositories.users import UsersRepo as _UsersRepo

    settings = get_settings()
    is_ticket = False
    raw: str | None = None
    if authorization and authorization.lower().startswith("bearer "):
        raw = authorization.split(" ", 1)[1].strip()
    elif ticket:
        raw = ticket.strip()
        is_ticket = True
    if not raw:
        raise _InvalidToken("Authorization required")

    payload = decode_jwt(raw, secret=settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    if is_ticket:
        if payload.get("purpose") != "export":
            raise _InvalidToken("Ticket not valid for this endpoint")
        # Bind ticket to URL: kind matches path suffix, params match query.
        expected_kind = "csv" if request.url.path.endswith(".csv") else "xlsx"
        if payload.get("kind") != expected_kind:
            raise _InvalidToken("Ticket kind mismatch")
        expected_params = {
            "from": request.query_params.get("from"),
            "to": request.query_params.get("to"),
            "staff_id": request.query_params.get("staff_id"),
        }
        actual_params = payload.get("params") or {}
        if actual_params != expected_params:
            raise _InvalidToken("Ticket params mismatch")
    elif payload.get("purpose") == "export":
        # Download-scoped ticket must NOT be accepted via Authorization header;
        # forces the leak path (Referer/logs) to also pass our purpose check.
        raise _InvalidToken("Export ticket must use ?ticket=")

    user_id_raw = payload.get("sub")
    if user_id_raw is None:
        raise _InvalidToken("Token missing subject")
    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError) as exc:
        raise _InvalidToken("Token subject malformed") from exc

    user = await _UsersRepo(session).get_by_id(user_id)
    if user is None:
        raise _InvalidToken("User not found")
    if user.role not in {UserRole.ADMIN, UserRole.SUPERADMIN}:
        raise _Forbidden("Admin role required")
    return user


from pydantic import BaseModel as _BaseModel  # noqa: E402


class _ExportTicketRequest(_BaseModel):
    kind: str  # 'csv' | 'xlsx'
    date_from: str | None = None
    date_to: str | None = None
    staff_id: int | None = None


class _ExportTicketResponse(_BaseModel):
    ticket: str
    expires_at: datetime


@router.post("/exports/ticket", response_model=_ExportTicketResponse)
async def issue_export_ticket(
    body: _ExportTicketRequest, admin: AdminUser
) -> _ExportTicketResponse:
    """Mint a short-lived (60s), purpose-scoped ticket for an export URL.

    Replaces the previous ?token=<full-admin-JWT> pattern. The ticket is bound
    to a specific export kind + params, so leakage via Referer/logs cannot be
    replayed against any other endpoint.
    """
    from fastapi import HTTPException

    from app.core.security import issue_download_ticket

    if body.kind not in ("csv", "xlsx"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="kind must be csv or xlsx"
        )
    settings = get_settings()
    params = {
        "from": body.date_from,
        "to": body.date_to,
        "staff_id": str(body.staff_id) if body.staff_id is not None else None,
    }
    ttl = timedelta(seconds=60)
    ticket = issue_download_ticket(
        subject=str(admin.id),
        role=admin.role.value,
        kind=body.kind,
        params=params,
        secret=settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
        expires_in=ttl,
    )
    return _ExportTicketResponse(
        ticket=ticket, expires_at=datetime.now(UTC) + ttl
    )


@router.get("/exports/bookings.csv")
async def export_bookings_csv(
    session: SessionDep,
    _admin: Annotated[User, Depends(_resolve_admin_for_export)],
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
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
            "Referrer-Policy": "no-referrer",
        },
    )


@router.get("/exports/bookings.xlsx")
async def export_bookings_xlsx(
    session: SessionDep,
    _admin: Annotated[User, Depends(_resolve_admin_for_export)],
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
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
            "Referrer-Policy": "no-referrer",
        },
    )


# ---------------------------------------------------------------------------
# Admin team / invites
# ---------------------------------------------------------------------------


async def _resolve_bot_username(request: Request, settings: Settings) -> str:
    """Return the bot's @username for invite URLs.

    Order of preference:
    1. Cached on app.state by the lifespan (set via bot.get_me()).
    2. Settings.BOT_USERNAME from env.
    3. Live call to bot.get_me() (and cache the result).
    4. Final fallback "your_bot" so the URL is at least well-formed.
    """
    cached: str | None = getattr(request.app.state, "bot_username", None)
    if cached:
        return cached
    if settings.BOT_USERNAME:
        request.app.state.bot_username = settings.BOT_USERNAME
        return settings.BOT_USERNAME
    bot = getattr(request.app.state, "bot", None)
    if bot is not None:
        try:
            me = await bot.get_me()
            if me.username:
                request.app.state.bot_username = me.username
                return me.username
        except Exception:
            pass
    return "your_bot"


def _build_invite_url(token: str, bot_username: str) -> str:
    return f"https://t.me/{bot_username}?start=invite_{token}"


@router.get("/team", response_model=TeamResponse)
async def admin_team(
    _admin: AdminUser, session: SessionDep, request: Request
) -> TeamResponse:
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
    bot_username = await _resolve_bot_username(request, settings)
    invites = [
        AdminInviteRead(
            id=i.id,
            token=i.token,
            role=i.role,
            created_at=i.created_at,
            expires_at=i.expires_at,
            url=_build_invite_url(i.token, bot_username),
        )
        for i in invites_raw
    ]
    return TeamResponse(members=members, invites=invites)


@router.post("/invites", response_model=AdminInviteRead, status_code=status.HTTP_201_CREATED)
async def admin_create_invite(
    body: AdminInviteCreate, admin: AdminUser, session: SessionDep, request: Request
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
    bot_username = await _resolve_bot_username(request, settings)
    return AdminInviteRead(
        id=invite.id,
        token=invite.token,
        role=invite.role,
        created_at=invite.created_at,
        expires_at=invite.expires_at,
        url=_build_invite_url(invite.token, bot_username),
    )


@router.delete("/invites/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_revoke_invite(
    invite_id: int, _admin: AdminUser, session: SessionDep
) -> None:
    ok = await AdminInvitesRepo(session).revoke(invite_id)
    if not ok:
        raise NotFound("Invite not found or already used")
    await session.commit()


@router.patch("/team/{user_id}/role", response_model=TeamMember)
async def admin_set_member_role(
    user_id: int,
    body: TeamMemberRoleUpdate,
    admin: AdminUser,
    session: SessionDep,
) -> TeamMember:
    """Change a team member's role. SUPERADMIN-protected and self-protected."""
    from fastapi import HTTPException
    target = await UsersRepo(session).get_by_id(user_id)
    if target is None:
        raise NotFound("User not found")
    if target.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя изменить собственную роль",
        )
    if target.role == UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нельзя менять роль главного администратора",
        )
    new_role = UserRole(body.role)
    target.role = new_role
    # If demoted from staff to anything else, unlink from any StaffMember.
    if new_role != UserRole.STAFF:
        from sqlalchemy import update as _update
        await session.execute(
            _update(StaffMember)
            .where(StaffMember.user_id == target.id)
            .values(user_id=None)
        )
    await session.commit()
    await session.refresh(target)
    return TeamMember.model_validate(target)


@router.delete("/team/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_remove_member(
    user_id: int, admin: AdminUser, session: SessionDep
) -> None:
    """Remove a member from the team — demote to client + unlink staff."""
    from fastapi import HTTPException
    from sqlalchemy import update as _update
    target = await UsersRepo(session).get_by_id(user_id)
    if target is None:
        raise NotFound("User not found")
    if target.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить себя из команды",
        )
    if target.role == UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нельзя удалить главного администратора",
        )
    target.role = UserRole.CLIENT
    await session.execute(
        _update(StaffMember)
        .where(StaffMember.user_id == target.id)
        .values(user_id=None)
    )
    await session.commit()


@router.get("/users", response_model=list[UserBrief])
async def admin_list_users(
    _admin: AdminUser,
    session: SessionDep,
    role: UserRole | None = None,
    linkable_only: bool = False,
    include_user_id: int | None = None,
) -> list[UserBrief]:
    users = await UsersRepo(session).list_for_linking(
        role=role,
        linkable_only=linkable_only,
        include_user_id=include_user_id,
    )
    return [UserBrief.model_validate(u) for u in users]


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


# ---------------------------------------------------------------------------
# Admin photo management (upload intent, sort, delete)
# ---------------------------------------------------------------------------


@router.post(
    "/photos/upload-intent",
    response_model=PhotoUploadIntentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_photo_upload_intent(
    body: PhotoUploadIntentCreate,
    admin: AdminUser,
    session: SessionDep,
    request: Request,
) -> PhotoUploadIntentResponse:
    if body.owner_type == PhotoOwnerType.SERVICE:
        owner = await ServicesRepo(session).get(body.owner_id)
    else:
        owner = await StaffRepo(session).get(body.owner_id)
    if owner is None:
        raise NotFound("Owner not found")

    intent = await PendingPhotoUploadsRepo(session).upsert(
        admin_user_id=admin.id,
        owner_type=body.owner_type,
        owner_id=body.owner_id,
    )
    await session.commit()

    settings = get_settings()
    bot_username = await _resolve_bot_username(request, settings)
    return PhotoUploadIntentResponse(
        bot_url=f"https://t.me/{bot_username}?start=upload",
        expires_at=intent.expires_at,
    )


@router.patch("/photos/{photo_id}/sort", response_model=dict)
async def admin_update_photo_sort(
    photo_id: int,
    body: PhotoSortUpdate,
    _admin: AdminUser,
    session: SessionDep,
) -> dict:
    photo = await PhotosRepo(session).get(photo_id)
    if photo is None:
        raise NotFound("Photo not found")
    photo.sort_order = body.sort_order
    await session.commit()
    return {"id": photo.id, "sort_order": photo.sort_order}


@router.delete("/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_photo(
    photo_id: int, _admin: AdminUser, session: SessionDep
) -> None:
    photo = await PhotosRepo(session).get(photo_id)
    if photo is None:
        raise NotFound("Photo not found")
    await PhotosRepo(session).delete(photo)
    await session.commit()


# ---------------------------------------------------------------------------
# Admin reviews moderation
# ---------------------------------------------------------------------------

from app.db.models.review import Review as _Review  # noqa: E402
from app.db.repositories.reviews import ReviewsRepo as _ReviewsRepo  # noqa: E402
from app.schemas.reviews import (  # noqa: E402
    AdminReviewReplyRequest as _ReplyReq,
)
from app.schemas.reviews import (  # noqa: E402
    ReviewRead as _ReviewRead,
)
from app.services.reviews_service import ReviewsService as _ReviewsService  # noqa: E402


@router.get("/reviews", response_model=list[_ReviewRead])
async def admin_list_reviews(
    _admin: AdminUser,
    session: SessionDep,
    hidden: bool | None = None,
    service_id: int | None = None,
    staff_id: int | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[_ReviewRead]:
    rows = await _ReviewsRepo(session).list_admin(
        hidden=hidden, service_id=service_id, staff_id=staff_id,
        limit=limit, offset=offset,
    )
    users_repo = UsersRepo(session)
    out: list[_ReviewRead] = []
    for r in rows:
        u = await users_repo.get_by_id(r.client_id)
        out.append(_ReviewRead(
            id=r.id, booking_id=r.booking_id, service_id=r.service_id,
            staff_id=r.staff_id, rating=r.rating, text=r.text,
            is_hidden=r.is_hidden, admin_reply=r.admin_reply,
            admin_reply_at=r.admin_reply_at, created_at=r.created_at,
            client_first_name=u.first_name if u else None,
        ))
    return out


async def _moderate_review(session, review_id: int, *, hide: bool) -> _Review:
    repo = _ReviewsRepo(session)
    r = await repo.get(review_id)
    if r is None:
        raise NotFound("Review not found")
    r.is_hidden = hide
    await session.commit()
    await _ReviewsService(session).recompute_aggregates(
        service_id=r.service_id, staff_id=r.staff_id
    )
    await session.commit()
    return r


@router.post("/reviews/{review_id}/hide", response_model=dict)
async def admin_hide_review(
    review_id: int, _admin: AdminUser, session: SessionDep
) -> dict:
    r = await _moderate_review(session, review_id, hide=True)
    return {"id": r.id, "is_hidden": True}


@router.post("/reviews/{review_id}/unhide", response_model=dict)
async def admin_unhide_review(
    review_id: int, _admin: AdminUser, session: SessionDep
) -> dict:
    r = await _moderate_review(session, review_id, hide=False)
    return {"id": r.id, "is_hidden": False}


@router.post("/reviews/{review_id}/reply", response_model=dict)
async def admin_reply_review(
    review_id: int, body: _ReplyReq, admin: AdminUser, session: SessionDep
) -> dict:
    r = await _ReviewsRepo(session).get(review_id)
    if r is None:
        raise NotFound("Review not found")
    r.admin_reply = body.text
    r.admin_reply_user_id = admin.id
    r.admin_reply_at = datetime.now(UTC)
    await session.commit()
    return {"id": r.id, "admin_reply": r.admin_reply}


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_review(
    review_id: int, _admin: AdminUser, session: SessionDep
) -> None:
    repo = _ReviewsRepo(session)
    r = await repo.get(review_id)
    if r is None:
        raise NotFound("Review not found")
    service_id, staff_id = r.service_id, r.staff_id
    await repo.delete(r)
    await session.commit()
    await _ReviewsService(session).recompute_aggregates(
        service_id=service_id, staff_id=staff_id
    )
    await session.commit()


# ---------------------------------------------------------------------------
# REVIEW_REQUEST enqueue helper (shared by admin_patch_booking + staff_me.patch_my_booking)
# ---------------------------------------------------------------------------

from sqlalchemy.exc import IntegrityError as _IntegrityError  # noqa: E402

from app.db.enums import (  # noqa: E402
    NotificationStatus as _NotificationStatus,
)
from app.db.enums import (  # noqa: E402
    NotificationType as _NotificationType,
)
from app.db.models.notification import Notification as _Notification  # noqa: E402


async def _enqueue_review_request(session, *, booking, previous_status: str) -> None:
    """Schedule a REVIEW_REQUEST notification 2h after booking marks completed.

    Idempotent — `ux_review_request_per_booking` partial UNIQUE index dedups
    repeated completion (e.g. admin clicks Завершить twice).
    Respects per-user opt-out via `users.reminders_enabled`.
    """
    if booking.status != BookingStatus.COMPLETED or previous_status == "completed":
        return
    client = await UsersRepo(session).get_by_id(booking.client_id)
    if client is None or not client.reminders_enabled:
        return
    try:
        session.add(_Notification(
            booking_id=booking.id,
            user_id=booking.client_id,
            notification_type=_NotificationType.REVIEW_REQUEST,
            notification_status=_NotificationStatus.PENDING,
            scheduled_at=datetime.now(UTC) + timedelta(hours=2),
        ))
        await session.commit()
    except _IntegrityError:
        await session.rollback()
