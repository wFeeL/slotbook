from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import CurrentUser, SessionDep
from app.core.rate_limit import rate_limit_booking_create
from app.db.enums import BookingSource, BookingStatus, UserRole
from app.db.repositories.bookings import BookingsRepo
from app.db.repositories.businesses import BusinessesRepo
from app.schemas.bookings import BookingCreate, BookingRead, BookingReschedule
from app.services.booking_service import BookingService
from app.services.notification_service import NotificationService

log = structlog.get_logger()

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post(
    "",
    response_model=BookingRead,
    status_code=201,
    dependencies=[Depends(rate_limit_booking_create)],
)
async def create_booking(
    body: BookingCreate,
    user: CurrentUser,
    session: SessionDep,
    request: Request,
) -> BookingRead:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    booking = await BookingService(session).create_booking(
        business=business,
        actor_user_id=user.id,
        client_id=user.id,
        staff_id=body.staff_id,
        service_id=body.service_id,
        starts_at=body.starts_at,
        client_comment=body.client_comment,
        source=BookingSource.MINI_APP,
    )
    try:
        await NotificationService(session, request.app.state.bot).dispatch_pending_for_booking(
            booking.id
        )
    except Exception:
        log.exception("notification.dispatch_failed_in_route", booking_id=booking.id)
    return BookingRead.model_validate(booking)


@router.get("/my", response_model=list[BookingRead])
async def my_bookings(
    user: CurrentUser,
    session: SessionDep,
    status: BookingStatus | None = Query(default=None),
) -> list[BookingRead]:
    bookings = await BookingsRepo(session).list_for_client(user.id, status=status)
    return [BookingRead.model_validate(b) for b in bookings]


@router.post("/{booking_id}/cancel", response_model=BookingRead)
async def cancel_booking(
    booking_id: int,
    user: CurrentUser,
    session: SessionDep,
    request: Request,
) -> BookingRead:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    # /bookings/* are client-facing. Force CLIENT role so booking_service enforces
    # ownership (booking.client_id == actor_user_id) and the cancellation window.
    # Admins use /admin/*, staff use /staff/me/* routes for their own bookings.
    booking = await BookingService(session).cancel_booking(
        business=business,
        actor_user_id=user.id,
        actor_role=UserRole.CLIENT,
        booking_id=booking_id,
    )
    try:
        await NotificationService(session, request.app.state.bot).dispatch_pending_for_booking(
            booking.id
        )
    except Exception:
        log.exception("notification.dispatch_failed_in_route", booking_id=booking.id)
    return BookingRead.model_validate(booking)


@router.post("/{booking_id}/reschedule", response_model=BookingRead)
async def reschedule_my_booking(
    booking_id: int,
    body: BookingReschedule,
    user: CurrentUser,
    session: SessionDep,
    request: Request,
) -> BookingRead:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    booking = await BookingService(session).reschedule_booking(
        business=business,
        actor_user_id=user.id,
        actor_role=UserRole.CLIENT,
        booking_id=booking_id,
        new_starts_at=body.starts_at,
    )
    try:
        await NotificationService(session, request.app.state.bot).dispatch_pending_for_booking(
            booking.id
        )
    except Exception:
        log.exception("notification.dispatch_failed_in_route", booking_id=booking.id)
    return BookingRead.model_validate(booking)
