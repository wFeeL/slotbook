from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.service import Service


class ServicesRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_active(
        self, business_id: int, branch_id: int | None = None
    ) -> list[Service]:
        stmt = select(Service).where(
            Service.business_id == business_id, Service.is_active.is_(True)
        )
        if branch_id is not None:
            stmt = stmt.where(Service.branch_id == branch_id)
        stmt = stmt.order_by(Service.sort_order, Service.title)
        return list((await self.session.execute(stmt)).scalars().all())

    async def get(self, service_id: int) -> Service | None:
        return await self.session.get(Service, service_id)

    async def list_all(self, business_id: int) -> list[Service]:
        stmt = (
            select(Service)
            .where(Service.business_id == business_id)
            .order_by(Service.sort_order, Service.title)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    def add(self, service: Service) -> None:
        self.session.add(service)

    async def soft_delete(self, service: Service) -> None:
        service.is_active = False
        await self.session.flush()
