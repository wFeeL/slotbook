from __future__ import annotations

from datetime import UTC, datetime, timedelta

MAX_RETRIES = 5


def backoff_delay(retry_count: int) -> timedelta:
    """Exponential backoff capped at 60 minutes.

    retry_count=0 -> 1m, 1 -> 2m, 2 -> 4m, 3 -> 8m, 4 -> 16m, 5+ -> 60m.
    """
    minutes = min(2**retry_count, 60)
    return timedelta(minutes=minutes)


def next_retry_at(retry_count: int, now: datetime | None = None) -> datetime:
    return (now or datetime.now(UTC)) + backoff_delay(retry_count)
