from datetime import UTC, datetime, time, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.db.enums import BookingSource, BookingStatus
from app.db.models.booking import Booking
from app.db.models.schedule import WorkingHours
from app.db.models.service import Service
from app.db.models.staff import StaffMember, StaffService
from tests.bot.conftest import make_callback_update

# superadmin_user fixture is defined in tests/conftest.py (session-level conftest)


@pytest_asyncio.fixture
async def seeded_booking(db_session, business, client_user):  # type: ignore[no-untyped-def]
    svc = Service(business_id=business.id, title="X", duration_minutes=60)
    staff = StaffMember(business_id=business.id, name="Eve")
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
    start = (datetime.now(UTC) + timedelta(days=2)).replace(minute=0, second=0, microsecond=0)
    b = Booking(
        business_id=business.id,
        client_id=client_user.id,
        staff_id=staff.id,
        service_id=svc.id,
        starts_at=start,
        ends_at=start + timedelta(hours=1),
        status=BookingStatus.CONFIRMED,
        source=BookingSource.MINI_APP,
    )
    db_session.add(b)
    await db_session.commit()
    await db_session.refresh(b)
    return b


@pytest.mark.asyncio
async def test_admin_cancels_booking(
    feed, db_session, admin_user, mock_bot, seeded_booking
) -> None:
    booking_id = seeded_booking.id  # capture before any session state changes
    update = make_callback_update(
        data=f"cancel_booking:{booking_id}",
        from_user_id=admin_user.telegram_id,
    )
    await feed(update)

    # The dispatcher committed its own session; expire our session's identity map
    # so the next query goes to the DB rather than returning the cached object.
    db_session.sync_session.expire_all()
    refreshed = (
        await db_session.execute(select(Booking).where(Booking.id == booking_id))
    ).scalar_one()
    assert refreshed.status == BookingStatus.CANCELLED_BY_ADMIN
    # Notifications must have been dispatched (B2 fix). The mock bot should
    # have been used to send at least one message (BOOKING_CANCELLED_CLIENT
    # and/or BOOKING_CANCELLED_ADMIN).
    assert mock_bot.send_message.await_count >= 1


@pytest.mark.asyncio
async def test_client_role_cannot_cancel_via_callback(
    feed, db_session, client_user, mock_bot, seeded_booking
) -> None:
    update = make_callback_update(
        data=f"cancel_booking:{seeded_booking.id}",
        from_user_id=client_user.telegram_id,
    )
    await feed(update)

    # Status must be UNCHANGED — client was rejected at the auth gate
    refreshed = (
        await db_session.execute(select(Booking).where(Booking.id == seeded_booking.id))
    ).scalar_one()
    assert refreshed.status == BookingStatus.CONFIRMED


@pytest.mark.asyncio
async def test_nonexistent_booking_does_not_crash(feed, admin_user, mock_bot, business) -> None:
    update = make_callback_update(
        data="cancel_booking:999999",
        from_user_id=admin_user.telegram_id,
    )
    await feed(update)  # should not raise


@pytest.mark.asyncio
async def test_malformed_callback_data(feed, admin_user, mock_bot, business) -> None:
    update = make_callback_update(
        data="cancel_booking:abc",
        from_user_id=admin_user.telegram_id,
    )
    await feed(update)  # should not raise


@pytest.mark.asyncio
async def test_admin_or_superadmin_can_cancel_admin(
    feed, db_session, mock_bot, seeded_booking, admin_user
) -> None:
    booking_id = seeded_booking.id  # capture before any session state changes
    update = make_callback_update(
        data=f"cancel_booking:{booking_id}",
        from_user_id=admin_user.telegram_id,
    )
    await feed(update)
    db_session.sync_session.expire_all()
    refreshed = (
        await db_session.execute(select(Booking).where(Booking.id == booking_id))
    ).scalar_one()
    assert refreshed.status == BookingStatus.CANCELLED_BY_ADMIN


@pytest.mark.asyncio
async def test_admin_or_superadmin_can_cancel_superadmin(
    feed, db_session, mock_bot, seeded_booking, superadmin_user
) -> None:
    booking_id = seeded_booking.id  # capture before any session state changes
    update = make_callback_update(
        data=f"cancel_booking:{booking_id}",
        from_user_id=superadmin_user.telegram_id,
    )
    await feed(update)
    db_session.sync_session.expire_all()
    refreshed = (
        await db_session.execute(select(Booking).where(Booking.id == booking_id))
    ).scalar_one()
    assert refreshed.status == BookingStatus.CANCELLED_BY_ADMIN
