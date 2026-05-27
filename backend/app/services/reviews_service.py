from __future__ import annotations

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.service import Service
from app.db.models.staff import StaffMember
from app.db.repositories.reviews import ReviewsRepo


class ReviewsService:
    """Encapsulates side-effects of review writes — denormalized aggregates."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def recompute_aggregates(self, *, service_id: int, staff_id: int) -> None:
        repo = ReviewsRepo(self.session)
        svc_avg, svc_count = await repo.aggregate_for_service(service_id)
        stf_avg, stf_count = await repo.aggregate_for_staff(staff_id)

        svc = await self.session.get(Service, service_id)
        if svc is not None:
            svc.avg_rating = Decimal(f"{svc_avg:.1f}") if svc_avg is not None else None
            svc.review_count = svc_count

        stf = await self.session.get(StaffMember, staff_id)
        if stf is not None:
            stf.avg_rating = Decimal(f"{stf_avg:.1f}") if stf_avg is not None else None
            stf.review_count = stf_count

        await self.session.flush()
