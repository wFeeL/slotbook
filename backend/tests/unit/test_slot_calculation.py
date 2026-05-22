from datetime import UTC, date, datetime, time

import pytest

from app.db.enums import ScheduleExceptionType
from app.services.slot_service import (
    BusyInterval,
    ExceptionEntry,
    Slot,
    WorkingInterval,
    calculate_available_slots,
)

TZ = "Europe/Moscow"  # UTC+3 year-round (no DST)


def _utc(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=UTC)


def _common(**kwargs) -> list[Slot]:  # type: ignore[no-untyped-def]
    defaults: dict = {
        "target_date": date(2026, 6, 15),
        "business_timezone": TZ,
        "service_duration_minutes": 60,
        "slot_step_minutes": 60,
        "buffer_minutes": 0,
        "working_hours": [WorkingInterval(time(10, 0), time(18, 0))],
        "exceptions": [],
        "bookings": [],
        "now_utc": _utc(2026, 1, 1, 0, 0),  # far in the past so nothing is filtered out
    }
    defaults.update(kwargs)
    return calculate_available_slots(**defaults)


# ---------------------------------------------------------------------------
# Test 1: Empty working hours - empty list
# ---------------------------------------------------------------------------
def test_empty_working_hours() -> None:
    result = _common(working_hours=[])
    assert result == []


# ---------------------------------------------------------------------------
# Test 2: Full working day 10-18, no bookings, 60-min service, 60-min step
#         -> 8 slots starting at UTC 7:00..14:00  (Moscow = UTC+3)
# ---------------------------------------------------------------------------
def test_full_working_day_no_bookings() -> None:
    slots = _common()
    starts = [s.starts_at_utc for s in slots]
    assert len(starts) == 8
    assert starts[0] == _utc(2026, 6, 15, 7, 0)
    assert starts[-1] == _utc(2026, 6, 15, 14, 0)


# ---------------------------------------------------------------------------
# Test 3: Booking at UTC 9-10 blocks the overlapping local 12-13 slot (UTC 9)
# ---------------------------------------------------------------------------
def test_booking_in_middle_blocks_overlapping_slots() -> None:
    booking = BusyInterval(start=_utc(2026, 6, 15, 9, 0), end=_utc(2026, 6, 15, 10, 0))
    slots = _common(bookings=[booking])
    starts = [s.starts_at_utc for s in slots]
    # UTC 9:00 slot (local 12:00-13:00) must be blocked
    assert _utc(2026, 6, 15, 9, 0) not in starts


# ---------------------------------------------------------------------------
# Test 4: Buffer 15 min - booking UTC 9-10 also blocks UTC 8:00 slot
#         because 8:00+60min=9:00 and expanded busy start = 9:00-15min = 8:45
#         -> 8:00 slot [8:00, 9:00) overlaps [8:45, 10:15) -> must be removed
# ---------------------------------------------------------------------------
def test_buffer_blocks_adjacent_slots() -> None:
    booking = BusyInterval(start=_utc(2026, 6, 15, 9, 0), end=_utc(2026, 6, 15, 10, 0))
    slots = _common(bookings=[booking], buffer_minutes=15)
    starts = [s.starts_at_utc for s in slots]
    # UTC 8:00 slot ends at 9:00; expanded busy starts at 8:45.
    # Overlap: cursor(8:00) < busy.end(10:15) AND slot_end(9:00) > busy.start(8:45) -> True
    assert _utc(2026, 6, 15, 8, 0) not in starts


# ---------------------------------------------------------------------------
# Test 5: DAY_OFF exception - empty list
# ---------------------------------------------------------------------------
def test_day_off_returns_no_slots() -> None:
    slots = _common(
        exceptions=[ExceptionEntry(type=ScheduleExceptionType.DAY_OFF, start=None, end=None)]
    )
    assert slots == []


# ---------------------------------------------------------------------------
# Test 6: EXTRA_WORKING_TIME 18-20 local adds UTC 15:00 and 16:00 slots
# ---------------------------------------------------------------------------
def test_extra_working_time_adds_slots() -> None:
    slots = _common(
        working_hours=[WorkingInterval(time(10, 0), time(12, 0))],
        exceptions=[
            ExceptionEntry(
                type=ScheduleExceptionType.EXTRA_WORKING_TIME,
                start=time(18, 0),
                end=time(20, 0),
            )
        ],
    )
    starts = [s.starts_at_utc for s in slots]
    assert _utc(2026, 6, 15, 15, 0) in starts  # 18:00 Moscow = 15:00 UTC
    assert _utc(2026, 6, 15, 16, 0) in starts  # 19:00 Moscow = 16:00 UTC


# ---------------------------------------------------------------------------
# Test 7: BLOCKED_TIME 12-14 local removes those slots; 11:00 local
#         (UTC 8:00) stays because it ends exactly at 12:00 (block start)
# ---------------------------------------------------------------------------
def test_blocked_time_removes_sub_interval() -> None:
    slots = _common(
        exceptions=[
            ExceptionEntry(
                type=ScheduleExceptionType.BLOCKED_TIME,
                start=time(12, 0),
                end=time(14, 0),
            )
        ]
    )
    starts = [s.starts_at_utc for s in slots]
    # UTC 9:00 (local 12:00-13:00) removed
    assert _utc(2026, 6, 15, 9, 0) not in starts
    # UTC 10:00 (local 13:00-14:00) removed
    assert _utc(2026, 6, 15, 10, 0) not in starts
    # UTC 8:00 (local 11:00-12:00) still present - ends exactly at block boundary
    assert _utc(2026, 6, 15, 8, 0) in starts


# ---------------------------------------------------------------------------
# Test 8: now_utc filter drops past slots
# ---------------------------------------------------------------------------
def test_today_drops_past_slots() -> None:
    slots = _common(now_utc=_utc(2026, 6, 15, 12, 0))  # noon UTC = 15:00 Moscow
    starts = [s.starts_at_utc for s in slots]
    assert all(s >= _utc(2026, 6, 15, 12, 0) for s in starts)
    assert _utc(2026, 6, 15, 7, 0) not in starts


# ---------------------------------------------------------------------------
# Test 9: Slot must fit entirely inside working window - small 60-min window
#         gives exactly one slot at the start
# ---------------------------------------------------------------------------
def test_slot_must_fit_inside_working_window() -> None:
    slots = _common(working_hours=[WorkingInterval(time(10, 0), time(11, 0))])
    starts = [s.starts_at_utc for s in slots]
    # 10:00-11:00 local = 07:00-08:00 UTC; one 60-min slot exactly fills it
    assert starts == [_utc(2026, 6, 15, 7, 0)]


# ---------------------------------------------------------------------------
# Bonus: 15-min step with 60-min duration -> 25 slots in a 7-hour window
# ---------------------------------------------------------------------------
def test_step_smaller_than_duration() -> None:
    # Use a 7-hour window: 10:00-17:00 local.
    # Last valid start: 16:00 (16:00+60min=17:00 <= 17:00).
    # Steps from 10:00 to 16:00 at 15-min intervals: (6*60)/15 + 1 = 24 + 1 = 25.
    slots = _common(
        slot_step_minutes=15,
        working_hours=[WorkingInterval(time(10, 0), time(17, 0))],
    )
    assert len(slots) == 25


# ---------------------------------------------------------------------------
# Extra: zero/negative service_duration_minutes -> empty
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("duration", [0, -1, -60])
def test_zero_or_negative_duration_returns_empty(duration: int) -> None:
    slots = _common(service_duration_minutes=duration)
    assert slots == []
