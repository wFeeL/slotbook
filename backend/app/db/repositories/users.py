from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import UserRole
from app.db.models.user import User


class UsersRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def upsert_from_telegram(
        self,
        *,
        telegram_id: int,
        first_name: str | None,
        last_name: str | None,
        username: str | None,
        admin_telegram_ids: set[int],
    ) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        now = datetime.now(UTC)
        if user is None:
            role = UserRole.ADMIN if telegram_id in admin_telegram_ids else UserRole.CLIENT
            user = User(
                telegram_id=telegram_id,
                first_name=first_name,
                last_name=last_name,
                username=username,
                role=role,
                last_seen_at=now,
            )
            self.session.add(user)
            await self.session.flush()
            return user

        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        user.last_seen_at = now
        # Promote CLIENTs to ADMIN if their Telegram ID is in the admin allowlist.
        # Never touch existing ADMINs or SUPERADMINs — in particular, a SUPERADMIN
        # whose telegram_id happens to be in BOT_ADMIN_TELEGRAM_IDS must NOT be
        # downgraded to ADMIN on the next login.
        if telegram_id in admin_telegram_ids and user.role == UserRole.CLIENT:
            user.role = UserRole.ADMIN
        await self.session.flush()
        return user

    async def list_for_linking(
        self,
        *,
        role: UserRole | None = None,
        linkable_only: bool = False,
        include_user_id: int | None = None,
    ) -> list[User]:
        from app.db.models.staff import StaffMember

        stmt = select(User)
        if role is not None:
            stmt = stmt.where(User.role == role)

        if linkable_only:
            allowed_roles = {UserRole.STAFF, UserRole.ADMIN, UserRole.SUPERADMIN}
            stmt = stmt.where(User.role.in_(allowed_roles))
            linked_subq = select(StaffMember.user_id).where(
                StaffMember.user_id.is_not(None),
                StaffMember.is_active.is_(True),
            )
            if include_user_id is not None:
                stmt = stmt.where(
                    (User.id.not_in(linked_subq)) | (User.id == include_user_id)
                )
            else:
                stmt = stmt.where(User.id.not_in(linked_subq))

        stmt = stmt.order_by(User.created_at.desc()).limit(200)
        return list((await self.session.execute(stmt)).scalars().all())
