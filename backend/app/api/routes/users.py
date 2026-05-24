from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import CurrentUser, SessionDep
from app.db.enums import UserRole

router = APIRouter(prefix="/users", tags=["users"])


class MePreferences(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    reminders_enabled: bool


class MePreferencesUpdate(BaseModel):
    reminders_enabled: bool = Field(...)


class MeResponse(BaseModel):
    id: int
    telegram_id: int
    first_name: str | None
    last_name: str | None
    username: str | None
    phone: str | None
    role: UserRole
    reminders_enabled: bool


@router.get("/me", response_model=MeResponse)
async def get_me(user: CurrentUser) -> MeResponse:
    return MeResponse(
        id=user.id,
        telegram_id=user.telegram_id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        phone=user.phone,
        role=user.role,
        reminders_enabled=user.reminders_enabled,
    )


@router.patch("/me/preferences", response_model=MePreferences)
async def patch_my_preferences(
    body: MePreferencesUpdate, user: CurrentUser, session: SessionDep
) -> MePreferences:
    user.reminders_enabled = body.reminders_enabled
    await session.commit()
    await session.refresh(user)
    return MePreferences(reminders_enabled=user.reminders_enabled)
