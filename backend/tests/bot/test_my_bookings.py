from datetime import UTC, datetime, time, timedelta

import pytest

from app.db.enums import BookingSource, BookingStatus
from app.db.models.booking import Booking
from app.db.models.schedule import WorkingHours
from app.db.models.service import Service
from app.db.models.staff import StaffMember, StaffService
from tests.bot.conftest import make_message_update


@pytest.mark.asyncio
async def test_my_bookings_empty(feed, mock_bot, business, client_user) -> None:
    update = make_message_update("/my_bookings", from_user_id=client_user.telegram_id, update_id=10)
    await feed(update)
    mock_bot.assert_called()


@pytest.mark.asyncio
async def test_my_bookings_lists_upcoming(
    feed, db_session, business, client_user, mock_bot
) -> None:
    branch_id = business._default_branch_id
    svc = Service(business_id=business.id, branch_id=branch_id, title="Cut", duration_minutes=60)
    staff = StaffMember(business_id=business.id, branch_id=branch_id, name="Eve")
    db_session.add_all([svc, staff])
    await db_session.flush()
    db_session.add(StaffService(staff_id=staff.id, service_id=svc.id))
    for d in range(7):
        db_session.add(
            WorkingHours(
                staff_id=staff.id,
                weekday=d,
                start_time=time(0, 0),
                end_time=time(23, 0),
                is_active=True,
            )
        )
    future_start = datetime.now(UTC) + timedelta(days=2)
    future_start = future_start.replace(minute=0, second=0, microsecond=0)
    db_session.add(
        Booking(
            business_id=business.id,
            branch_id=branch_id,
            client_id=client_user.id,
            staff_id=staff.id,
            service_id=svc.id,
            starts_at=future_start,
            ends_at=future_start + timedelta(hours=1),
            status=BookingStatus.CONFIRMED,
            source=BookingSource.MINI_APP,
        )
    )
    await db_session.commit()

    update = make_message_update("/my_bookings", from_user_id=client_user.telegram_id, update_id=11)
    await feed(update)
    mock_bot.assert_called()
