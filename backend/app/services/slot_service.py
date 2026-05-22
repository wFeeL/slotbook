from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from datetime import date as date_t
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFound, ServiceInactive, StaffDoesNotOfferService, StaffInactive
from app.core.time import local_date_bounds_utc, to_business_local
from app.db.enums import ScheduleExceptionType
from app.db.models.business import Business
from app.db.repositories.bookings import BookingsRepo
from app.db.repositories.schedules import ScheduleExceptionsRepo, WorkingHoursRepo
from app.db.repositories.services import ServicesRepo
from app.db.repositories.staff import StaffRepo


@dataclass(frozen=True, slots=True)
class WorkingInterval:
    """Local-time interval [start, end) for a single day."""

    start: time
    end: time


@dataclass(frozen=True, slots=True)
class BusyInterval:
    """UTC interval already occupied; caller must NOT pre-expand by buffer (the algorithm does it)."""

    start: datetime
    end: datetime


@dataclass(frozen=True, slots=True)
class ExceptionEntry:
    type: ScheduleExceptionType
    start: time | None
    end: time | None


@dataclass(frozen=True, slots=True)
class Slot:
    starts_at_utc: datetime
    ends_at_utc: datetime


def _interval_minus(
    working: list[tuple[time, time]], cut: tuple[time, time]
) -> list[tuple[time, time]]:
    """Subtract half-open interval `cut` from each interval in `working`.

    Semantics are half-open [start, end).  A cut that touches an interval
    boundary does NOT remove the boundary slot.
    """
    result: list[tuple[time, time]] = []
    for w_start, w_end in working:
        c_start, c_end = cut
        # No overlap
        if c_end <= w_start or c_start >= w_end:
            result.append((w_start, w_end))
            continue
        # Left remainder
        if c_start > w_start:
            result.append((w_start, c_start))
        # Right remainder
        if c_end < w_end:
            result.append((c_end, w_end))
    return result


def _apply_exceptions(
    base: list[WorkingInterval],
    exceptions: list[ExceptionEntry],
) -> list[tuple[time, time]]:
    """Return effective working intervals after applying all exceptions.

    Order of operations:
      1. If any DAY_OFF exception exists → return [].
      2. Collect base intervals + EXTRA_WORKING_TIME intervals, sort, merge.
      3. Subtract each BLOCKED_TIME interval from the merged set.
    """
    has_day_off = any(e.type == ScheduleExceptionType.DAY_OFF for e in exceptions)
    if has_day_off:
        return []

    intervals: list[tuple[time, time]] = [(w.start, w.end) for w in base]
    for ex in exceptions:
        if ex.type == ScheduleExceptionType.EXTRA_WORKING_TIME and ex.start and ex.end:
            intervals.append((ex.start, ex.end))

    intervals.sort()

    # Merge overlapping / adjacent intervals
    merged: list[tuple[time, time]] = []
    for s, e in intervals:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))

    # Subtract BLOCKED_TIME intervals
    for ex in exceptions:
        if ex.type == ScheduleExceptionType.BLOCKED_TIME and ex.start and ex.end:
            merged = _interval_minus(merged, (ex.start, ex.end))

    return merged


def calculate_available_slots(
    *,
    target_date: date_t,
    business_timezone: str,
    service_duration_minutes: int,
    slot_step_minutes: int,
    buffer_minutes: int,
    working_hours: list[WorkingInterval],
    exceptions: list[ExceptionEntry],
    bookings: list[BusyInterval],
    now_utc: datetime,
) -> list[Slot]:
    """Return all available slots for `target_date` given the inputs.

    Pure function — no I/O, no ``datetime.now()`` calls.  All time logic is
    deterministic given the explicit ``now_utc`` parameter.

    Half-open interval semantics throughout: ``[start, end)``.
    """
    if service_duration_minutes <= 0:
        return []

    if slot_step_minutes <= 0:
        return []

    tz = ZoneInfo(business_timezone)
    effective_intervals = _apply_exceptions(working_hours, exceptions)
    if not effective_intervals:
        return []

    # Expand busy intervals by buffer on both sides.
    expanded_busy: list[BusyInterval] = [
        BusyInterval(
            start=b.start - timedelta(minutes=buffer_minutes),
            end=b.end + timedelta(minutes=buffer_minutes),
        )
        for b in bookings
    ]

    duration = timedelta(minutes=service_duration_minutes)
    step = timedelta(minutes=slot_step_minutes)
    slots: list[Slot] = []

    for w_start_t, w_end_t in effective_intervals:
        local_start = datetime.combine(target_date, w_start_t, tzinfo=tz)
        local_end = datetime.combine(target_date, w_end_t, tzinfo=tz)
        utc_start = local_start.astimezone(UTC)
        utc_end = local_end.astimezone(UTC)

        cursor = utc_start
        while cursor + duration <= utc_end:
            slot_end = cursor + duration

            # Drop past slots
            if cursor < now_utc:
                cursor += step
                continue

            # Drop slots that overlap any expanded busy interval
            collides = any(cursor < busy.end and slot_end > busy.start for busy in expanded_busy)
            if not collides:
                slots.append(Slot(starts_at_utc=cursor, ends_at_utc=slot_end))

            cursor += step

    slots.sort(key=lambda s: s.starts_at_utc)
    return slots


class SlotService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_available_slots(
        self,
        business: Business,
        service_id: int,
        staff_id: int,
        target_date: date_t,
        now_utc: datetime | None = None,
    ) -> list[dict[str, datetime]]:
        service = await ServicesRepo(self.session).get(service_id)
        if service is None:
            raise NotFound("Service not found")
        if not service.is_active:
            raise ServiceInactive()

        staff = await StaffRepo(self.session).get(staff_id)
        if staff is None:
            raise NotFound("Staff member not found")
        if not staff.is_active:
            raise StaffInactive()
        if not await StaffRepo(self.session).offers_service(staff_id, service_id):
            raise StaffDoesNotOfferService()

        wh_rows = await WorkingHoursRepo(self.session).list_for_staff_weekday(
            staff_id, target_date.weekday()
        )
        working_intervals = [WorkingInterval(r.start_time, r.end_time) for r in wh_rows]

        exc_rows = await ScheduleExceptionsRepo(self.session).list_for_staff_date(
            staff_id, target_date
        )
        exceptions = [
            ExceptionEntry(type=e.type, start=e.start_time, end=e.end_time) for e in exc_rows
        ]

        start_utc, end_utc = local_date_bounds_utc(target_date, business.timezone)
        bookings = await BookingsRepo(self.session).list_active_for_staff_range(
            staff_id, start_utc, end_utc
        )
        busy = [BusyInterval(start=b.starts_at, end=b.ends_at) for b in bookings]

        now = now_utc or datetime.now(UTC)
        raw_slots = calculate_available_slots(
            target_date=target_date,
            business_timezone=business.timezone,
            service_duration_minutes=service.duration_minutes,
            slot_step_minutes=business.slot_step_minutes,
            buffer_minutes=business.booking_buffer_minutes,
            working_hours=working_intervals,
            exceptions=exceptions,
            bookings=busy,
            now_utc=now,
        )
        return [
            {
                "starts_at": s.starts_at_utc,
                "ends_at": s.ends_at_utc,
                "starts_at_local": to_business_local(s.starts_at_utc, business.timezone),
                "ends_at_local": to_business_local(s.ends_at_utc, business.timezone),
            }
            for s in raw_slots
        ]
