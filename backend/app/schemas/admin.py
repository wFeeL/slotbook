from __future__ import annotations

from datetime import datetime

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator

from app.db.enums import BookingStatus


class AdminBookingPatch(BaseModel):
    admin_comment: str | None = Field(default=None, max_length=2000)
    status: BookingStatus | None = None


class AdminBookingCreate(BaseModel):
    client_telegram_id: int
    service_id: int = Field(gt=0)
    staff_id: int = Field(gt=0)
    starts_at: AwareDatetime
    client_comment: str | None = Field(default=None, max_length=1000)
    admin_comment: str | None = Field(default=None, max_length=2000)


class AdminBookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    branch_id: int
    client_id: int
    service_id: int
    staff_id: int
    starts_at: datetime
    ends_at: datetime
    status: BookingStatus
    client_comment: str | None
    admin_comment: str | None
    # Enriched fields populated at the route layer via lookup tables.
    service_title: str | None = None
    staff_name: str | None = None
    client_first_name: str | None = None
    client_last_name: str | None = None
    client_telegram_id: int | None = None


class DashboardCounts(BaseModel):
    today: int
    this_week: int
    no_show_30d: int


class DashboardResponse(BaseModel):
    counts: DashboardCounts


class BusinessRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    timezone: str
    booking_buffer_minutes: int
    min_cancellation_hours: int
    slot_step_minutes: int
    reminder_long_hours: int
    reminder_short_hours: int


class BusinessUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    timezone: str | None = None
    booking_buffer_minutes: int | None = Field(default=None, ge=0, le=60)
    min_cancellation_hours: int | None = Field(default=None, ge=0, le=168)
    slot_step_minutes: int | None = None
    reminder_long_hours: int | None = Field(default=None, ge=1, le=168)
    reminder_short_hours: int | None = Field(default=None, ge=0, le=24)

    @field_validator("slot_step_minutes")
    @classmethod
    def _step_allowed(cls, v: int | None) -> int | None:
        if v is not None and v not in {5, 10, 15, 20, 30, 60}:
            raise ValueError("slot_step_minutes must be one of 5/10/15/20/30/60")
        return v

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
