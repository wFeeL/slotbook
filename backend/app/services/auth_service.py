from __future__ import annotations

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import issue_jwt
from app.core.telegram_auth import validate_init_data
from app.db.models.user import User
from app.db.repositories.users import UsersRepo


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.users = UsersRepo(session)

    async def authenticate_telegram(self, init_data_raw: str) -> tuple[str, int, User]:
        payload = validate_init_data(self.settings.BOT_TOKEN, init_data_raw)
        user = await self.users.upsert_from_telegram(
            telegram_id=payload.telegram_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            username=payload.username,
            admin_telegram_ids=set(self.settings.BOT_ADMIN_TELEGRAM_IDS),
        )
        await self.session.commit()
        await self.session.refresh(user)

        expires_in_minutes = self.settings.JWT_EXPIRE_MINUTES
        token = issue_jwt(
            subject=str(user.id),
            role=user.role.value,
            secret=self.settings.JWT_SECRET,
            algorithm=self.settings.JWT_ALGORITHM,
            expires_in=timedelta(minutes=expires_in_minutes),
        )
        return token, expires_in_minutes * 60, user
