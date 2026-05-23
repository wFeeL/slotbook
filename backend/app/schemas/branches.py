from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BranchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    address: str | None
    timezone: str
    is_active: bool
    sort_order: int


class BranchCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    address: str | None = Field(default=None, max_length=500)
    timezone: str
    sort_order: int = 0

    @field_validator("timezone")
    @classmethod
    def _tz_valid(cls, v: str) -> str:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        try:
            ZoneInfo(v)
        except ZoneInfoNotFoundError:
            raise ValueError(f"Unknown timezone: {v}") from None
        return v


class BranchUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    address: str | None = Field(default=None, max_length=500)
    timezone: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None

    @field_validator("timezone")
    @classmethod
    def _tz_valid(cls, v: str | None) -> str | None:
        if v is None:
            return v
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        try:
            ZoneInfo(v)
        except ZoneInfoNotFoundError:
            raise ValueError(f"Unknown timezone: {v}") from None
        return v
