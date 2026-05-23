from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.staff import StaffMember, StaffService


class StaffRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_service(
        self, business_id: int, service_id: int, branch_id: int | None = None
    ) -> list[StaffMember]:
        stmt = (
            select(StaffMember)
            .join(StaffService, StaffMember.id == StaffService.staff_id)
            .where(
                StaffMember.business_id == business_id,
                StaffMember.is_active.is_(True),
                StaffService.service_id == service_id,
            )
        )
        if branch_id is not None:
            stmt = stmt.where(StaffMember.branch_id == branch_id)
        stmt = stmt.order_by(StaffMember.name)
        return list((await self.session.execute(stmt)).scalars().all())

    async def list_all(self, business_id: int) -> list[StaffMember]:
        stmt = (
            select(StaffMember)
            .where(StaffMember.business_id == business_id)
            .order_by(StaffMember.name)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def get(self, staff_id: int) -> StaffMember | None:
        return await self.session.get(StaffMember, staff_id)

    def add(self, staff: StaffMember) -> None:
        self.session.add(staff)

    async def replace_services(self, staff_id: int, service_ids: list[int]) -> None:
        await self.session.execute(delete(StaffService).where(StaffService.staff_id == staff_id))
        for sid in service_ids:
            self.session.add(StaffService(staff_id=staff_id, service_id=sid))
        await self.session.flush()

    async def offers_service(self, staff_id: int, service_id: int) -> bool:
        stmt = (
            select(StaffService)
            .where(StaffService.staff_id == staff_id, StaffService.service_id == service_id)
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none() is not None

    async def list_for_business(
        self, business_id: int, include_archived: bool = True
    ) -> list[StaffMember]:
        stmt = select(StaffMember).where(StaffMember.business_id == business_id)
        if not include_archived:
            stmt = stmt.where(StaffMember.is_active.is_(True))
        stmt = stmt.order_by(StaffMember.id)
        return list((await self.session.execute(stmt)).scalars().all())

    async def list_service_ids(self, staff_id: int) -> list[int]:
        stmt = select(StaffService.service_id).where(StaffService.staff_id == staff_id)
        return list((await self.session.execute(stmt)).scalars().all())
