"""SlotBook seed script.

Usage:
  python seed.py                     # ensure the singleton Business exists
  python seed.py --demo              # also insert demo services/staff/booking (idempotent)
  python seed.py --demo --clean      # purge the demo Business and reseed from scratch
  python seed.py --clean --force     # required if APP_ENV=prod
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal

import structlog
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.enums import BookingSource, UserRole
from app.db.models.booking import Booking
from app.db.models.schedule import WorkingHours
from app.db.models.service import Service
from app.db.models.staff import StaffMember, StaffService
from app.db.models.user import User
from app.db.repositories.businesses import BusinessesRepo
from app.db.session import get_engine

log = structlog.get_logger()


async def _purge(session) -> None:
    """Delete all Bookings / Services / Staff / WorkingHours for the singleton business."""
    biz = await BusinessesRepo(session).get_singleton()
    if biz is None:
        log.info("seed.clean_noop")
        return
    # FK cascades will handle most of these, but delete explicitly for clarity.
    await session.execute(delete(Booking).where(Booking.business_id == biz.id))
    await session.execute(delete(StaffService))  # global join table
    await session.execute(delete(WorkingHours))  # global table; SP1 says one business
    await session.execute(delete(StaffMember).where(StaffMember.business_id == biz.id))
    await session.execute(delete(Service).where(Service.business_id == biz.id))
    await session.commit()
    log.info("seed.purged", business_id=biz.id)


async def seed(demo: bool, clean: bool) -> None:
    settings = get_settings()
    configure_logging(settings)
    sessionmaker = async_sessionmaker(get_engine(), expire_on_commit=False)

    async with sessionmaker() as session:
        if clean:
            await _purge(session)

        biz = await BusinessesRepo(session).ensure_from_settings(
            name=settings.BUSINESS_NAME,
            timezone=settings.BUSINESS_TIMEZONE,
            booking_buffer_minutes=settings.BUSINESS_BOOKING_BUFFER_MINUTES,
            min_cancellation_hours=settings.BUSINESS_MIN_CANCELLATION_HOURS,
            slot_step_minutes=settings.BUSINESS_SLOT_STEP_MINUTES,
        )
        await session.commit()
        log.info("seed.business_ready", id=biz.id, name=biz.name)

        if not demo:
            return

        from sqlalchemy import select

        existing_demo_service = (
            await session.execute(select(Service).where(Service.business_id == biz.id).limit(1))
        ).scalar_one_or_none()
        if existing_demo_service is not None:
            log.info("seed.demo_already_present")
            return

        haircut = Service(
            business_id=biz.id,
            title="Стрижка",
            duration_minutes=60,
            price=Decimal("1500.00"),
        )
        consult = Service(
            business_id=biz.id,
            title="Консультация",
            duration_minutes=45,
            price=Decimal("2000.00"),
        )
        session.add_all([haircut, consult])
        await session.flush()

        master = StaffMember(business_id=biz.id, name="Алексей")
        session.add(master)
        await session.flush()
        session.add_all(
            [
                StaffService(staff_id=master.id, service_id=haircut.id),
                StaffService(staff_id=master.id, service_id=consult.id),
            ]
        )
        for weekday in range(5):
            session.add(
                WorkingHours(
                    staff_id=master.id,
                    weekday=weekday,
                    start_time=time(10, 0),
                    end_time=time(18, 0),
                    is_active=True,
                )
            )

        demo_client = User(telegram_id=10001, first_name="Демо", role=UserRole.CLIENT)
        session.add(demo_client)
        await session.flush()

        future = datetime.now(UTC) + timedelta(days=1, hours=2)
        future = future.replace(minute=0, second=0, microsecond=0)
        session.add(
            Booking(
                business_id=biz.id,
                client_id=demo_client.id,
                staff_id=master.id,
                service_id=haircut.id,
                starts_at=future,
                ends_at=future + timedelta(minutes=haircut.duration_minutes),
                source=BookingSource.ADMIN_MANUAL,
            )
        )
        await session.commit()
        log.info("seed.demo_complete")


def main() -> None:
    parser = argparse.ArgumentParser(description="SlotBook seed script")
    parser.add_argument("--demo", action="store_true", help="Also seed demo data (idempotent)")
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Purge demo data before seeding. Refuses on APP_ENV=prod unless --force.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Required to use --clean when APP_ENV=prod.",
    )
    args = parser.parse_args()

    if args.clean and get_settings().APP_ENV == "prod" and not args.force:
        raise SystemExit("Refusing to --clean in production without --force.")

    asyncio.run(seed(demo=args.demo, clean=args.clean))


if __name__ == "__main__":
    main()
