from __future__ import annotations

from datetime import date as date_t

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.schedule import ScheduleException, WorkingHours


class WorkingHoursRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_staff(self, staff_id: int) -> list[WorkingHours]:
        stmt = (
            select(WorkingHours)
            .where(WorkingHours.staff_id == staff_id)
            .order_by(WorkingHours.weekday)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def list_for_staff_weekday(self, staff_id: int, weekday: int) -> list[WorkingHours]:
        stmt = select(WorkingHours).where(
            WorkingHours.staff_id == staff_id,
            WorkingHours.weekday == weekday,
            WorkingHours.is_active.is_(True),
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def replace_for_staff(self, staff_id: int, entries: list[WorkingHours]) -> None:
        await self.session.execute(delete(WorkingHours).where(WorkingHours.staff_id == staff_id))
        for entry in entries:
            entry.staff_id = staff_id
            self.session.add(entry)
        await self.session.flush()


class ScheduleExceptionsRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_staff_date(self, staff_id: int, day: date_t) -> list[ScheduleException]:
        stmt = select(ScheduleException).where(
            ScheduleException.staff_id == staff_id,
            ScheduleException.date == day,
        )
        return list((await self.session.execute(stmt)).scalars().all())

    def add(self, exception: ScheduleException) -> None:
        self.session.add(exception)

    async def delete(self, exception_id: int) -> bool:
        result = await self.session.execute(
            delete(ScheduleException).where(ScheduleException.id == exception_id)
        )
        return bool(result.rowcount > 0)  # type: ignore[attr-defined]
