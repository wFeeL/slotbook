from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

import structlog
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.notifications import NotificationsRepo
from app.services.notification_service import NotificationService

log = structlog.get_logger()

SessionFactory = Callable[[], AsyncSession]


async def tick(session_factory: SessionFactory, bot: Bot, *, limit: int = 200) -> int:
    """Process one batch of due-pending notifications. Returns the count sent."""
    now_utc = datetime.now(UTC)
    sent = 0
    async with session_factory() as session:
        due = await NotificationsRepo(session).list_pending_due(now_utc, limit=limit)
        if not due:
            return 0
        # Group by booking_id so we can fan out via NotificationService per booking
        booking_ids = sorted({n.booking_id for n in due if n.booking_id is not None})
        log.info("worker.tick", due_count=len(due), bookings=len(booking_ids))
        for bid in booking_ids:
            try:
                await NotificationService(session, bot).dispatch_pending_for_booking(bid)
                sent += 1
            except Exception:  # noqa: BLE001
                log.exception("worker.dispatch_failed", booking_id=bid)
        # Notifications service commits internally; no further commit needed here.
    return sent
