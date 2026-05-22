from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo


def to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        raise ValueError("Refusing to convert naive datetime")
    return dt.astimezone(UTC)


def to_business_local(dt: datetime, tz_name: str) -> datetime:
    if dt.tzinfo is None:
        raise ValueError("Refusing to convert naive datetime")
    return dt.astimezone(ZoneInfo(tz_name))


def local_date_bounds_utc(target_date: date, tz_name: str) -> tuple[datetime, datetime]:
    """Return [start_of_day_utc, start_of_next_day_utc) for target_date in tz_name."""
    tz = ZoneInfo(tz_name)
    start_local = datetime.combine(target_date, time.min, tzinfo=tz)
    end_local = datetime.combine(target_date + timedelta(days=1), time.min, tzinfo=tz)
    return start_local.astimezone(UTC), end_local.astimezone(UTC)


def business_now_utc(now: datetime | None = None) -> datetime:
    if now is None:
        return datetime.now(UTC)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return now.astimezone(UTC)
