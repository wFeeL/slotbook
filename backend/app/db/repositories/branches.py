from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.branch import Branch


class BranchesRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_business(
        self, business_id: int, include_archived: bool = False
    ) -> list[Branch]:
        stmt = select(Branch).where(Branch.business_id == business_id)
        if not include_archived:
            stmt = stmt.where(Branch.is_active.is_(True))
        stmt = stmt.order_by(Branch.sort_order, Branch.id)
        return list((await self.session.execute(stmt)).scalars().all())

    async def get(self, branch_id: int) -> Branch | None:
        return await self.session.get(Branch, branch_id)

    async def get_default(self, business_id: int) -> Branch | None:
        stmt = (
            select(Branch)
            .where(Branch.business_id == business_id, Branch.is_active.is_(True))
            .order_by(Branch.sort_order, Branch.id)
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    def add(self, branch: Branch) -> None:
        self.session.add(branch)
