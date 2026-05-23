from __future__ import annotations

from datetime import UTC, datetime

from app.bot.texts import render
from app.db.enums import BookingStatus, NotificationType
from app.db.models.booking import Booking
from app.db.models.business import Business
from app.db.models.notification import Notification
from app.db.models.service import Service
from app.db.models.staff import StaffMember
from app.db.models.user import User


def _fixture():
    starts = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)
    booking = Booking(
        id=1,
        business_id=1,
        branch_id=1,
        client_id=1,
        service_id=1,
        staff_id=1,
        starts_at=starts,
        ends_at=starts,
        status=BookingStatus.CONFIRMED,
        client_comment=None,
    )
    service = Service(
        id=1, business_id=1, branch_id=1, title="Стрижка",
        duration_minutes=30, price="1000",
    )
    staff = StaffMember(id=1, business_id=1, branch_id=1, name="Анна")
    business = Business(id=1, name="Studio", timezone="UTC")
    client = User(id=1, telegram_id=10, first_name="Иван")
    return booking, service, staff, business, client


def test_render_booking_created_staff_includes_client_name():
    booking, service, staff, business, client = _fixture()
    n = Notification(notification_type=NotificationType.BOOKING_CREATED_STAFF, user_id=1)
    text, kb = render(
        n, booking=booking, service=service, staff=staff, business=business,
        mini_app_url="https://example.test", client=client,
    )
    assert "Иван" in text
    assert "Новая запись" in text
    assert "Стрижка" in text
    assert kb is not None


def test_render_booking_created_staff_without_client_falls_back():
    booking, service, staff, business, _ = _fixture()
    n = Notification(notification_type=NotificationType.BOOKING_CREATED_STAFF, user_id=1)
    text, _ = render(
        n, booking=booking, service=service, staff=staff, business=business,
        mini_app_url="https://example.test", client=None,
    )
    assert "Клиент" in text
    assert "Иван" not in text


def test_render_booking_cancelled_staff():
    booking, service, staff, business, client = _fixture()
    n = Notification(notification_type=NotificationType.BOOKING_CANCELLED_STAFF, user_id=1)
    text, _ = render(
        n, booking=booking, service=service, staff=staff, business=business,
        mini_app_url="https://example.test", client=client,
    )
    assert "отменена" in text.lower()


def test_render_booking_rescheduled_staff():
    booking, service, staff, business, client = _fixture()
    n = Notification(notification_type=NotificationType.BOOKING_RESCHEDULED_STAFF, user_id=1)
    text, _ = render(
        n, booking=booking, service=service, staff=staff, business=business,
        mini_app_url="https://example.test", client=client,
    )
    assert "перенесена" in text.lower()
