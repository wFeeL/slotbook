from __future__ import annotations

from datetime import datetime

from pydantic import AwareDatetime, BaseModel, Field

from app.db.enums import BookingStatus


class BookingCreate(BaseModel):
    service_id: int = Field(..., gt=0)
    staff_id: int = Field(..., gt=0)
    starts_at: AwareDatetime
    client_comment: str | None = Field(default=None, max_length=1000)


class BookingRead(BaseModel):
    id: int
    branch_id: int
    service_id: int
    staff_id: int
    starts_at: datetime
    ends_at: datetime
    status: BookingStatus
    client_comment: str | None

    model_config = {"from_attributes": True}


class BookingReschedule(BaseModel):
    starts_at: AwareDatetime
