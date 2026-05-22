from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import Forbidden, InvalidToken
from app.core.security import decode_jwt
from app.db.enums import UserRole
from app.db.models.user import User
from app.db.repositories.users import UsersRepo
from app.db.session import get_session

SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    session: SessionDep,
    settings: SettingsDep,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise InvalidToken("Authorization header missing")
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_jwt(token, secret=settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    user_id_raw = payload.get("sub")
    if user_id_raw is None:
        raise InvalidToken("Token missing subject")
    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError) as exc:
        raise InvalidToken("Token subject malformed") from exc

    user = await UsersRepo(session).get_by_id(user_id)
    if user is None:
        raise InvalidToken("User not found")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_admin_user(user: CurrentUser) -> User:
    if user.role not in {UserRole.ADMIN, UserRole.SUPERADMIN}:
        raise Forbidden("Admin role required")
    return user


AdminUser = Annotated[User, Depends(get_admin_user)]
