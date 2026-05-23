from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import UserRole
from app.db.models.admin_invite import AdminInvite


class AdminInvitesRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def generate_token() -> str:
        return secrets.token_urlsafe(24)

    async def create(
        self,
        *,
        business_id: int,
        role: UserRole,
        created_by_user_id: int,
        ttl_hours: int,
    ) -> AdminInvite:
        now = datetime.now(UTC)
        invite = AdminInvite(
            business_id=business_id,
            token=self.generate_token(),
            role=role.value,
            created_by_user_id=created_by_user_id,
            expires_at=now + timedelta(hours=ttl_hours),
        )
        self.session.add(invite)
        await self.session.flush()
        return invite

    async def list_active(self, business_id: int) -> list[AdminInvite]:
        now = datetime.now(UTC)
        stmt = (
            select(AdminInvite)
            .where(
                AdminInvite.business_id == business_id,
                AdminInvite.consumed_at.is_(None),
                AdminInvite.expires_at > now,
            )
            .order_by(AdminInvite.created_at.desc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_by_token(self, token: str) -> AdminInvite | None:
        stmt = select(AdminInvite).where(AdminInvite.token == token)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def revoke(self, invite_id: int) -> bool:
        result = await self.session.execute(
            update(AdminInvite)
            .where(AdminInvite.id == invite_id, AdminInvite.consumed_at.is_(None))
            .values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
        )
        return (result.rowcount or 0) > 0

    async def consume(self, invite: AdminInvite, user_id: int) -> None:
        invite.consumed_at = datetime.now(UTC)
        invite.consumed_by_user_id = user_id
        await self.session.flush()
