from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.business import Business


class BusinessesRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_singleton(self) -> Business | None:
        stmt = select(Business).order_by(Business.id).limit(1)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def ensure_from_settings(
        self,
        *,
        name: str,
        timezone: str,
        booking_buffer_minutes: int,
        min_cancellation_hours: int,
        slot_step_minutes: int,
    ) -> Business:
        existing = await self.get_singleton()
        if existing is not None:
            return existing
        business = Business(
            name=name,
            timezone=timezone,
            booking_buffer_minutes=booking_buffer_minutes,
            min_cancellation_hours=min_cancellation_hours,
            slot_step_minutes=slot_step_minutes,
        )
        self.session.add(business)
        await self.session.flush()
        return business
