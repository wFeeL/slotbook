from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import pytest

from app.core.time import (
    business_now_utc,
    local_date_bounds_utc,
    to_business_local,
    to_utc,
)


def test_to_utc_from_aware() -> None:
    moscow = ZoneInfo("Europe/Moscow")
    local = datetime(2026, 6, 15, 10, 0, tzinfo=moscow)
    assert to_utc(local) == datetime(2026, 6, 15, 7, 0, tzinfo=UTC)


def test_to_utc_rejects_naive() -> None:
    with pytest.raises(ValueError):
        to_utc(datetime(2026, 6, 15, 10, 0))


def test_to_business_local_returns_business_tz() -> None:
    moscow = ZoneInfo("Europe/Moscow")
    utc = datetime(2026, 6, 15, 7, 0, tzinfo=UTC)
    assert to_business_local(utc, "Europe/Moscow") == datetime(2026, 6, 15, 10, 0, tzinfo=moscow)


def test_local_date_bounds_utc_for_moscow() -> None:
    start, end = local_date_bounds_utc(date(2026, 6, 15), "Europe/Moscow")
    # Moscow is UTC+3 year-round.
    assert start == datetime(2026, 6, 14, 21, 0, tzinfo=UTC)
    assert end == datetime(2026, 6, 15, 21, 0, tzinfo=UTC)


def test_local_date_bounds_handles_dst_transition_london() -> None:
    # Last Sunday of March 2026 = 2026-03-29 — DST forward in London (BST starts).
    start, end = local_date_bounds_utc(date(2026, 3, 29), "Europe/London")
    # 00:00 BST didn't exist before transition; local midnight = 00:00 GMT = 00:00 UTC.
    # 24h-later in London = 23:00 UTC (because the day was 23 hours long).
    assert start == datetime(2026, 3, 29, 0, 0, tzinfo=UTC)
    assert end == datetime(2026, 3, 29, 23, 0, tzinfo=UTC)


def test_business_now_utc_uses_injected_clock() -> None:
    fixed = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    assert business_now_utc(now=fixed) == fixed
