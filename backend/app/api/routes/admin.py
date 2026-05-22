from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import AdminUser, SessionDep
from app.core.errors import CannotCancelInCurrentStatus, NotFound
from app.core.time import local_date_bounds_utc
from app.db.enums import BookingSource, BookingStatus, UserRole
from app.db.models.schedule import ScheduleException, WorkingHours
from app.db.models.service import Service
from app.db.models.staff import StaffMember
from app.db.models.user import User
from app.db.repositories.bookings import BookingsRepo
from app.db.repositories.businesses import BusinessesRepo
from app.db.repositories.schedules import ScheduleExceptionsRepo, WorkingHoursRepo
from app.db.repositories.services import ServicesRepo
from app.db.repositories.staff import StaffRepo
from app.db.repositories.users import UsersRepo
from app.schemas.admin import (
    AdminBookingCreate,
    AdminBookingPatch,
    AdminBookingRead,
    DashboardCounts,
    DashboardResponse,
)
from app.schemas.schedules import (
    ScheduleExceptionCreate,
    ScheduleExceptionRead,
    WorkingHoursEntry,
    WorkingHoursReplace,
)
from app.schemas.services import ServiceCreate, ServiceRead, ServiceUpdate
from app.schemas.staff import StaffCreate, StaffRead, StaffServicesUpdate, StaffUpdate
from app.services.booking_service import BookingService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/services", response_model=ServiceRead, status_code=status.HTTP_201_CREATED)
async def create_service(
    body: ServiceCreate, _admin: AdminUser, session: SessionDep
) -> ServiceRead:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    service = Service(
        business_id=business.id,
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


@router.post("/staff", response_model=StaffRead, status_code=status.HTTP_201_CREATED)
async def create_staff(body: StaffCreate, _admin: AdminUser, session: SessionDep) -> StaffRead:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    staff = StaffMember(business_id=business.id, name=body.name, description=body.description)
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


@router.get("/bookings", response_model=list[AdminBookingRead])
async def admin_list_bookings(
    admin: AdminUser,
    session: SessionDep,
    date_filter: Annotated[date | None, Query(alias="date")] = None,
    staff_id: int | None = None,
    service_id: int | None = None,
    status_filter: Annotated[BookingStatus | None, Query(alias="status")] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[AdminBookingRead]:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    repo = BookingsRepo(session)
    if date_filter is not None:
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
    return [AdminBookingRead.model_validate(b) for b in bookings]


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

    if body.status is not None:
        allowed = {BookingStatus.COMPLETED, BookingStatus.NO_SHOW}
        if body.status not in allowed:
            raise CannotCancelInCurrentStatus("Use the dedicated cancel endpoint for cancellation")
        booking.status = body.status

    await session.commit()
    await session.refresh(booking)
    return AdminBookingRead.model_validate(booking)


@router.post("/bookings", response_model=AdminBookingRead, status_code=status.HTTP_201_CREATED)
async def admin_create_booking(
    body: AdminBookingCreate,
    admin: AdminUser,
    session: SessionDep,
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

    return AdminBookingRead.model_validate(booking)


@router.post("/bookings/{booking_id}/cancel", response_model=AdminBookingRead)
async def admin_cancel_booking(
    booking_id: int,
    admin: AdminUser,
    session: SessionDep,
) -> AdminBookingRead:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    booking = await BookingService(session).cancel_booking(
        business=business,
        actor_user_id=admin.id,
        actor_role=admin.role,
        booking_id=booking_id,
    )
    return AdminBookingRead.model_validate(booking)


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
