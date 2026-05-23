from app.bot.keyboards import (
    admin_new_booking_keyboard,
    client_booking_created_keyboard,
    main_menu_keyboard,
    my_bookings_keyboard,
)

MINI = "https://app.example.com"


def test_main_menu_has_two_web_app_buttons() -> None:
    kb = main_menu_keyboard(MINI)
    flat = [btn for row in kb.inline_keyboard for btn in row]
    assert len(flat) == 2
    assert all(btn.web_app is not None for btn in flat)
    assert flat[0].web_app.url == MINI


def test_admin_new_booking_keyboard_callback_data() -> None:
    kb = admin_new_booking_keyboard(42, MINI)
    flat = [btn for row in kb.inline_keyboard for btn in row]
    cancel_btn = next(b for b in flat if b.callback_data is not None)
    assert cancel_btn.callback_data == "cancel_booking:42"
    web_btn = next(b for b in flat if b.web_app is not None)
    assert web_btn.web_app.url == f"{MINI}/admin/bookings/42"


def test_client_booking_created_keyboard_links_my_bookings() -> None:
    kb = client_booking_created_keyboard(MINI)
    btn = kb.inline_keyboard[0][0]
    assert btn.web_app.url == f"{MINI}/my-bookings"


def test_my_bookings_keyboard_strips_trailing_slash() -> None:
    kb = my_bookings_keyboard(MINI + "/")
    btn = kb.inline_keyboard[0][0]
    assert btn.web_app.url == f"{MINI}/my-bookings"
