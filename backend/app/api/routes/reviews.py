from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, SessionDep
from app.core.errors import Forbidden, NotFound
from app.db.enums import BookingStatus
from app.db.models.review import Review
from app.db.repositories.bookings import BookingsRepo
from app.db.repositories.reviews import ReviewsRepo
from app.db.repositories.users import UsersRepo
from app.schemas.reviews import ReviewCreate, ReviewRead
from app.services.reviews_service import ReviewsService

router = APIRouter(tags=["reviews"])


def _to_read(review: Review, client_name: str | None) -> ReviewRead:
    return ReviewRead(
        id=review.id,
        booking_id=review.booking_id,
        service_id=review.service_id,
        staff_id=review.staff_id,
        rating=review.rating,
        text=review.text,
        is_hidden=review.is_hidden,
        admin_reply=review.admin_reply,
        admin_reply_at=review.admin_reply_at,
        created_at=review.created_at,
        client_first_name=client_name,
    )


@router.post("/reviews", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
async def create_review(
    body: ReviewCreate, user: CurrentUser, session: SessionDep
) -> ReviewRead:
    booking = await BookingsRepo(session).get(body.booking_id)
    if booking is None:
        raise NotFound("Booking not found")
    if booking.client_id != user.id:
        raise Forbidden("Only the booking owner can review")
    if booking.status != BookingStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Can only review a completed booking",
        )

    review = Review(
        booking_id=booking.id,
        client_id=user.id,
        service_id=booking.service_id,
        staff_id=booking.staff_id,
        rating=body.rating,
        text=body.text,
    )
    ReviewsRepo(session).add(review)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        if "ux_reviews_booking" in str(exc.orig or exc):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Вы уже оценили эту встречу",
            ) from exc
        raise
    await session.refresh(review)

    await ReviewsService(session).recompute_aggregates(
        service_id=review.service_id, staff_id=review.staff_id,
    )
    await session.commit()

    return _to_read(review, user.first_name)


@router.get("/services/{service_id}/reviews", response_model=list[ReviewRead])
async def list_service_reviews(
    service_id: int,
    _user: CurrentUser,
    session: SessionDep,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ReviewRead]:
    rows = await ReviewsRepo(session).list_public_for_service(
        service_id, limit=limit, offset=offset
    )
    if not rows:
        return []
    users_repo = UsersRepo(session)
    out: list[ReviewRead] = []
    for r in rows:
        u = await users_repo.get_by_id(r.client_id)
        out.append(_to_read(r, u.first_name if u else None))
    return out


@router.get("/staff/{staff_id}/reviews", response_model=list[ReviewRead])
async def list_staff_reviews(
    staff_id: int,
    _user: CurrentUser,
    session: SessionDep,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ReviewRead]:
    rows = await ReviewsRepo(session).list_public_for_staff(
        staff_id, limit=limit, offset=offset
    )
    if not rows:
        return []
    users_repo = UsersRepo(session)
    out: list[ReviewRead] = []
    for r in rows:
        u = await users_repo.get_by_id(r.client_id)
        out.append(_to_read(r, u.first_name if u else None))
    return out
