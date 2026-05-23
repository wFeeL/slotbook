from __future__ import annotations

from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field

from app.db.enums import BookingStatus, ScheduleExceptionType


class StaffMeStaff(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    branch_id: int
    name: str
    description: str | None
    is_active: bool


class StaffMeBranch(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    timezone: str


class StaffMeResponse(BaseModel):
    linked: bool
    staff: StaffMeStaff | None = None
    branch: StaffMeBranch | None = None
    business_timezone: str


class StaffBookingRead(BaseModel):
    id: int
    starts_at: datetime
    ends_at: datetime
    status: BookingStatus
    service_id: int
    service_title: str
    service_duration_minutes: int
    service_price: str | None
    client_first_name: str | None
    client_last_name: str | None
    client_phone: str | None
    client_username: str | None
    client_comment: str | None
    admin_comment: str | None


class StaffBookingPatch(BaseModel):
    status: BookingStatus | None = None
    admin_comment: str | None = Field(default=None, max_length=2000)


class StaffScheduleInterval(BaseModel):
    start_time: time
    end_time: time


class StaffScheduleException(BaseModel):
    id: int
    date: date
    type: ScheduleExceptionType
    start_time: time | None
    end_time: time | None
    reason: str | None


class StaffScheduleBooking(BaseModel):
    id: int
    starts_at: datetime
    ends_at: datetime
    service_title: str
    client_first_name: str | None
    status: BookingStatus


class StaffScheduleDay(BaseModel):
    date: date
    weekday: int
    working_intervals: list[StaffScheduleInterval]
    exceptions: list[StaffScheduleException]
    bookings: list[StaffScheduleBooking]


class StaffScheduleResponse(BaseModel):
    week_start: date
    business_timezone: str
    days: list[StaffScheduleDay]
