from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    booking_id: int = Field(gt=0)
    rating: int = Field(ge=1, le=5)
    text: str | None = Field(default=None, max_length=2000)


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    booking_id: int
    service_id: int
    staff_id: int
    rating: int
    text: str | None
    is_hidden: bool
    admin_reply: str | None
    admin_reply_at: datetime | None
    created_at: datetime
    client_first_name: str | None = None


class AdminReviewReplyRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
