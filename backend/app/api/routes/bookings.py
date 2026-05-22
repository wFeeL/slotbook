from __future__ import annotations

from fastapi import APIRouter, Query, Request

from app.api.deps import CurrentUser, SessionDep
from app.db.enums import BookingSource, BookingStatus
from app.db.repositories.bookings import BookingsRepo
from app.db.repositories.businesses import BusinessesRepo
from app.schemas.bookings import BookingCreate, BookingRead
from app.services.booking_service import BookingService
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingRead, status_code=201)
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
    await NotificationService(session, request.app.state.bot).dispatch_pending_for_booking(
        booking.id
    )
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
    booking = await BookingService(session).cancel_booking(
        business=business,
        actor_user_id=user.id,
        actor_role=user.role,
        booking_id=booking_id,
    )
    await NotificationService(session, request.app.state.bot).dispatch_pending_for_booking(
        booking.id
    )
    return BookingRead.model_validate(booking)
