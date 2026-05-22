from datetime import datetime

from pydantic import BaseModel


class SlotRead(BaseModel):
    starts_at: datetime  # UTC
    ends_at: datetime  # UTC
    starts_at_local: datetime
    ends_at_local: datetime


class SlotsResponse(BaseModel):
    date: str
    timezone: str
    slots: list[SlotRead]
