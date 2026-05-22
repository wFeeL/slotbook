from datetime import date as date_t
from datetime import time

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.db.enums import ScheduleExceptionType


class WorkingHoursEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    weekday: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    is_active: bool = True

    @model_validator(mode="after")
    def _check_order(self) -> "WorkingHoursEntry":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class WorkingHoursReplace(BaseModel):
    entries: list[WorkingHoursEntry]


class ScheduleExceptionCreate(BaseModel):
    date: date_t
    type: ScheduleExceptionType
    start_time: time | None = None
    end_time: time | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def _validate_times(self) -> "ScheduleExceptionCreate":
        if self.type == ScheduleExceptionType.DAY_OFF:
            self.start_time = None
            self.end_time = None
        else:
            if self.start_time is None or self.end_time is None:
                raise ValueError(f"start_time/end_time required for type {self.type}")
            if self.end_time <= self.start_time:
                raise ValueError("end_time must be after start_time")
        return self


class ScheduleExceptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date_t
    start_time: time | None
    end_time: time | None
    type: ScheduleExceptionType
    reason: str | None
