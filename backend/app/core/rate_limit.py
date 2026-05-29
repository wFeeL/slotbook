"""In-process token-bucket rate limiter for DDoS-tier protection.

Deliberately generous: limits exist to absorb floods from a single
misbehaving client, never to throttle interactive use. A legitimate user
will never observe a 429 from these limits.

Storage: in-process dict. Multi-worker deployments may serve N× the
configured rate before the bucket triggers — acceptable because a single
process still bounds memory/CPU.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from fastapi import HTTPException, Request, status


@dataclass
class _Bucket:
    tokens: float
    last_refill: float


class TokenBucketLimiter:
    """Per-key token bucket. Thread-unsafe; relies on asyncio single-thread."""

    def __init__(self, *, capacity: int, refill_per_second: float) -> None:
        self.capacity = capacity
        self.refill_per_second = refill_per_second
        self._buckets: dict[str, _Bucket] = {}
        self._last_gc = time.monotonic()

    def _gc(self, now: float) -> None:
        # Drop buckets idle for > 10 minutes to bound memory.
        if now - self._last_gc < 60:
            return
        cutoff = now - 600
        stale = [k for k, b in self._buckets.items() if b.last_refill < cutoff]
        for k in stale:
            self._buckets.pop(k, None)
        self._last_gc = now

    def check(self, key: str) -> bool:
        now = time.monotonic()
        self._gc(now)
        b = self._buckets.get(key)
        if b is None:
            b = _Bucket(tokens=float(self.capacity), last_refill=now)
            self._buckets[key] = b
        elapsed = now - b.last_refill
        b.tokens = min(self.capacity, b.tokens + elapsed * self.refill_per_second)
        b.last_refill = now
        if b.tokens >= 1:
            b.tokens -= 1
            return True
        return False


def _client_ip(request: Request) -> str:
    # Trust the reverse proxy's X-Forwarded-For if present (Caddy/Nginx set it).
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    if request.client is None:
        return "unknown"
    return request.client.host


# Auth endpoint: bursts up to 30 req/IP, refills 1 req/sec.
# A real user issues at most one auth per session — generous by orders of magnitude.
_auth_limiter = TokenBucketLimiter(capacity=30, refill_per_second=1.0)


async def rate_limit_auth(request: Request) -> None:
    """Generous DDoS-tier limiter for /auth/telegram.

    A normal user authenticates once per session. 30-burst + 1/sec refill
    only stops obvious flood traffic.
    """
    key = f"auth:{_client_ip(request)}"
    if not _auth_limiter.check(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests",
            headers={"Retry-After": "5"},
        )


# Booking create: bursts up to 60 req/IP/min, refills 1/sec.
# A reasonable user may create a handful of bookings — 60 in a burst is unreachable
# without scripting.
_booking_limiter = TokenBucketLimiter(capacity=60, refill_per_second=1.0)


async def rate_limit_booking_create(request: Request) -> None:
    key = f"booking:{_client_ip(request)}"
    if not _booking_limiter.check(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests",
            headers={"Retry-After": "5"},
        )
