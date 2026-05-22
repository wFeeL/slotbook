from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.db.enums import BookingSource
from app.db.repositories.businesses import BusinessesRepo
from app.schemas.bookings import BookingCreate, BookingRead
from app.services.booking_service import BookingService

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingRead, status_code=201)
async def create_booking(
    body: BookingCreate,
    user: CurrentUser,
    session: SessionDep,
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
    return BookingRead.model_validate(booking)


@router.post("/{booking_id}/cancel", response_model=BookingRead)
async def cancel_booking(
    booking_id: int,
    user: CurrentUser,
    session: SessionDep,
) -> BookingRead:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    booking = await BookingService(session).cancel_booking(
        business=business,
        actor_user_id=user.id,
        actor_role=user.role,
        booking_id=booking_id,
    )
    return BookingRead.model_validate(booking)
