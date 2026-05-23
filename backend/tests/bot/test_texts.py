from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.bot.texts import render
from app.db.enums import (
    BookingSource,
    BookingStatus,
    NotificationStatus,
    NotificationType,
)
from app.db.models.booking import Booking
from app.db.models.business import Business
from app.db.models.notification import Notification
from app.db.models.service import Service
from app.db.models.staff import StaffMember

MINI = "https://app.example.com"


def _fixtures() -> tuple[Booking, Service, StaffMember, Business]:
    business = Business(id=1, name="Demo", timezone="Europe/Moscow")
    service = Service(
        id=10, business_id=1, title="Стрижка", duration_minutes=60, price=Decimal("1500")
    )
    staff = StaffMember(id=20, business_id=1, name="Алексей")
    booking = Booking(
        id=42,
        business_id=1,
        client_id=99,
        staff_id=staff.id,
        service_id=service.id,
        starts_at=datetime(2026, 6, 15, 7, 0, tzinfo=UTC),  # 10:00 Moscow
        ends_at=datetime(2026, 6, 15, 8, 0, tzinfo=UTC),
        status=BookingStatus.CONFIRMED,
        source=BookingSource.MINI_APP,
    )
    return booking, service, staff, business


def _notif(type_: NotificationType) -> Notification:
    return Notification(
        id=1,
        booking_id=42,
        user_id=99,
        notification_type=type_,
        notification_status=NotificationStatus.PENDING,
    )


def test_render_client_booking_created_includes_local_time_and_button() -> None:
    booking, service, staff, business = _fixtures()
    text, kb = render(
        _notif(NotificationType.BOOKING_CREATED_CLIENT),
        booking=booking,
        service=service,
        staff=staff,
        business=business,
        mini_app_url=MINI,
    )
    assert "10:00" in text  # Moscow local time
    assert "15 июня" in text
    assert "Стрижка" in text
    assert "Алексей" in text
    assert kb is not None  # has 'Мои записи' button


def test_render_admin_booking_created_includes_comment_and_cancel_button() -> None:
    booking, service, staff, business = _fixtures()
    booking.client_comment = "Хочу коротко"
    text, kb = render(
        _notif(NotificationType.BOOKING_CREATED_ADMIN),
        booking=booking,
        service=service,
        staff=staff,
        business=business,
        mini_app_url=MINI,
    )
    assert "Новая запись" in text
    assert "Хочу коротко" in text
    flat = [btn for row in kb.inline_keyboard for btn in row]
    assert any(b.callback_data == "cancel_booking:42" for b in flat)


def test_render_escapes_html_in_user_strings() -> None:
    booking, service, staff, business = _fixtures()
    booking.client_comment = "<script>alert(1)</script>"
    text, _kb = render(
        _notif(NotificationType.BOOKING_CREATED_ADMIN),
        booking=booking,
        service=service,
        staff=staff,
        business=business,
        mini_app_url=MINI,
    )
    assert "<script>" not in text
    assert "&lt;script&gt;" in text


def test_render_client_cancelled_has_no_keyboard() -> None:
    booking, service, staff, business = _fixtures()
    _text, kb = render(
        _notif(NotificationType.BOOKING_CANCELLED_CLIENT),
        booking=booking,
        service=service,
        staff=staff,
        business=business,
        mini_app_url=MINI,
    )
    assert kb is None


def test_render_unknown_type_raises() -> None:
    booking, service, staff, business = _fixtures()
    notif = _notif(NotificationType.BOOKING_CREATED_CLIENT)
    notif.notification_type = "bogus"  # type: ignore[assignment]
    with pytest.raises(ValueError, match="Unknown notification type"):
        render(
            notif,
            booking=booking,
            service=service,
            staff=staff,
            business=business,
            mini_app_url=MINI,
        )
