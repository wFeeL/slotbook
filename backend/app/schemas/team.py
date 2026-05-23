from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class TeamMember(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    telegram_id: int
    first_name: str | None
    last_name: str | None
    username: str | None
    role: str
    created_at: datetime


class AdminInviteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    token: str
    role: str
    created_at: datetime
    expires_at: datetime
    url: str  # computed


class TeamResponse(BaseModel):
    members: list[TeamMember]
    invites: list[AdminInviteRead]


class AdminInviteCreate(BaseModel):
    role: Literal["admin", "staff"]
    ttl_hours: Literal[24, 168, 720] = 168
