"""SlotBook seed script.

Usage:
  python seed.py                     # ensure the singleton Business exists
  python seed.py --demo              # also insert realistic salon demo data (idempotent)
  python seed.py --demo --clean      # purge demo data and reseed from scratch
  python seed.py --clean --force     # required if APP_ENV=prod
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal

import structlog
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.enums import BookingSource, UserRole
from app.db.models.booking import Booking
from app.db.models.branch import Branch
from app.db.models.schedule import WorkingHours
from app.db.models.service import Service
from app.db.models.staff import StaffMember, StaffService
from app.db.models.user import User
from app.db.repositories.businesses import BusinessesRepo
from app.db.session import get_engine

log = structlog.get_logger()


# Realistic beauty-studio service catalogue
DEMO_SERVICES = [
    {"title": "Женская стрижка", "duration": 60, "price": "2500", "desc": "Стрижка, мытьё головы, укладка феном."},
    {"title": "Мужская стрижка", "duration": 45, "price": "1500", "desc": "Машинка + ножницы, борода по запросу."},
    {"title": "Окрашивание в один тон", "duration": 120, "price": "5500", "desc": "Однотонное окрашивание корней + длина."},
    {"title": "Сложное окрашивание (балаяж)", "duration": 180, "price": "9500", "desc": "Балаяж / шатуш с тонированием."},
    {"title": "Укладка вечерняя", "duration": 60, "price": "2200", "desc": "Локоны / гладкая укладка под мероприятие."},
    {"title": "Маникюр гель-лак", "duration": 90, "price": "2800", "desc": "Аппаратный маникюр + покрытие гель-лаком."},
    {"title": "Педикюр", "duration": 75, "price": "2900", "desc": "Классический педикюр + покрытие."},
    {"title": "Массаж спины 30 мин", "duration": 30, "price": "1800", "desc": "Расслабляющий массаж воротниковой зоны и спины."},
]

# Realistic staff with specialisations
DEMO_STAFF = [
    {
        "name": "Анна Морозова",
        "description": "Колорист и стилист. 8 лет опыта в салонах премиум-сегмента.",
        "services": ["Женская стрижка", "Окрашивание в один тон", "Сложное окрашивание (балаяж)", "Укладка вечерняя"],
        "schedule": [(0, 10, 19), (1, 10, 19), (2, 11, 20), (3, 10, 19), (5, 10, 16)],
    },
    {
        "name": "Дмитрий Соколов",
        "description": "Барбер. Мужские стрижки, оформление бороды, классические причёски.",
        "services": ["Мужская стрижка"],
        "schedule": [(0, 11, 20), (1, 11, 20), (3, 11, 20), (4, 11, 20), (5, 10, 18)],
    },
    {
        "name": "Елена Иванова",
        "description": "Мастер маникюра и педикюра. Аппаратный, классический и комбинированный.",
        "services": ["Маникюр гель-лак", "Педикюр"],
        "schedule": [(0, 9, 18), (1, 9, 18), (2, 9, 18), (4, 11, 20), (5, 10, 17)],
    },
    {
        "name": "Михаил Кузнецов",
        "description": "Сертифицированный массажист. Спортивный, классический, расслабляющий массаж.",
        "services": ["Массаж спины 30 мин"],
        "schedule": [(1, 12, 21), (2, 12, 21), (3, 12, 21), (4, 12, 21), (6, 10, 18)],
    },
]


async def _purge(session) -> None:
    """Delete all Bookings / Services / Staff / WorkingHours for the singleton business."""
    biz = await BusinessesRepo(session).get_singleton()
    if biz is None:
        log.info("seed.clean_noop")
        return
    await session.execute(delete(Booking).where(Booking.business_id == biz.id))
    await session.execute(delete(StaffService))
    await session.execute(delete(WorkingHours))
    await session.execute(delete(StaffMember).where(StaffMember.business_id == biz.id))
    await session.execute(delete(Service).where(Service.business_id == biz.id))
    await session.commit()
    log.info("seed.purged", business_id=biz.id)


async def _ensure_default_branch(session, biz: object) -> Branch:
    """Make sure a default branch exists for the business."""
    branch = (
        await session.execute(
            select(Branch).where(Branch.business_id == biz.id).order_by(Branch.id).limit(1)
        )
    ).scalar_one_or_none()
    if branch is None:
        branch = Branch(
            business_id=biz.id, name=biz.name, timezone=biz.timezone, sort_order=0
        )
        session.add(branch)
        await session.flush()
    return branch


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

        branch = await _ensure_default_branch(session, biz)
        await session.commit()

        existing_demo_service = (
            await session.execute(
                select(Service).where(Service.business_id == biz.id).limit(1)
            )
        ).scalar_one_or_none()
        if existing_demo_service is not None:
            log.info("seed.demo_already_present")
            return

        # Services
        services_by_title: dict[str, Service] = {}
        for idx, item in enumerate(DEMO_SERVICES):
            svc = Service(
                business_id=biz.id,
                branch_id=branch.id,
                title=item["title"],
                description=item["desc"],
                duration_minutes=item["duration"],
                price=Decimal(item["price"]),
                sort_order=idx,
            )
            session.add(svc)
            services_by_title[item["title"]] = svc
        await session.flush()

        # Staff + their services + working hours
        for staff_def in DEMO_STAFF:
            staff = StaffMember(
                business_id=biz.id,
                branch_id=branch.id,
                name=staff_def["name"],
                description=staff_def["description"],
            )
            session.add(staff)
            await session.flush()
            for svc_title in staff_def["services"]:
                svc = services_by_title.get(svc_title)
                if svc is None:
                    continue
                session.add(StaffService(staff_id=staff.id, service_id=svc.id))
            for weekday, start_h, end_h in staff_def["schedule"]:
                session.add(
                    WorkingHours(
                        staff_id=staff.id,
                        weekday=weekday,
                        start_time=time(start_h, 0),
                        end_time=time(end_h, 0),
                        is_active=True,
                    )
                )

        # Demo client + sample bookings (one upcoming, one completed)
        demo_client = (
            await session.execute(
                select(User).where(User.telegram_id == 10001).limit(1)
            )
        ).scalar_one_or_none()
        if demo_client is None:
            demo_client = User(
                telegram_id=10001,
                first_name="Демо",
                last_name="Клиент",
                username="demo_client",
                role=UserRole.CLIENT,
            )
            session.add(demo_client)
            await session.flush()

        # Upcoming booking — tomorrow noon with first staff member
        first_staff = (
            await session.execute(
                select(StaffMember)
                .where(StaffMember.business_id == biz.id)
                .order_by(StaffMember.id)
                .limit(1)
            )
        ).scalar_one()
        first_service_title = next(
            (s for s in DEMO_STAFF[0]["services"] if s in services_by_title),
            None,
        )
        if first_service_title:
            svc = services_by_title[first_service_title]
            future = datetime.now(UTC).replace(
                minute=0, second=0, microsecond=0
            ) + timedelta(days=1, hours=2)
            session.add(
                Booking(
                    business_id=biz.id,
                    branch_id=branch.id,
                    client_id=demo_client.id,
                    staff_id=first_staff.id,
                    service_id=svc.id,
                    starts_at=future,
                    ends_at=future + timedelta(minutes=svc.duration_minutes),
                    source=BookingSource.ADMIN_MANUAL,
                )
            )

        await session.commit()
        log.info("seed.demo_complete", services=len(DEMO_SERVICES), staff=len(DEMO_STAFF))


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
