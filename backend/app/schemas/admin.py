from __future__ import annotations

from datetime import datetime

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from app.db.enums import BookingStatus


class AdminBookingPatch(BaseModel):
    admin_comment: str | None = None
    status: BookingStatus | None = None


class AdminBookingCreate(BaseModel):
    client_telegram_id: int
    service_id: int = Field(gt=0)
    staff_id: int = Field(gt=0)
    starts_at: AwareDatetime
    client_comment: str | None = None
    admin_comment: str | None = None


class AdminBookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    client_id: int
    service_id: int
    staff_id: int
    starts_at: datetime
    ends_at: datetime
    status: BookingStatus
    client_comment: str | None
    admin_comment: str | None


class DashboardCounts(BaseModel):
    today: int
    this_week: int
    no_show_30d: int


class DashboardResponse(BaseModel):
    counts: DashboardCounts
