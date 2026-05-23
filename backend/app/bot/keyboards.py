from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


def main_menu_keyboard(mini_app_url: str) -> InlineKeyboardMarkup:
    """Greeting menu shown after /start."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 Записаться", web_app=WebAppInfo(url=mini_app_url))],
            [
                InlineKeyboardButton(
                    text="📋 Мои записи",
                    web_app=WebAppInfo(url=f"{mini_app_url.rstrip('/')}/my-bookings"),
                )
            ],
        ]
    )


def client_booking_created_keyboard(mini_app_url: str) -> InlineKeyboardMarkup:
    """Single button under a client-side booking-created notification."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Мои записи",
                    web_app=WebAppInfo(url=f"{mini_app_url.rstrip('/')}/my-bookings"),
                )
            ]
        ]
    )


def admin_new_booking_keyboard(booking_id: int, mini_app_url: str) -> InlineKeyboardMarkup:
    """Inline buttons under an admin notification of a new booking."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Отменить", callback_data=f"cancel_booking:{booking_id}"
                ),
                InlineKeyboardButton(
                    text="📋 Открыть в панели",
                    web_app=WebAppInfo(
                        url=f"{mini_app_url.rstrip('/')}/admin/bookings/{booking_id}"
                    ),
                ),
            ]
        ]
    )


def my_bookings_keyboard(mini_app_url: str) -> InlineKeyboardMarkup:
    """Single 'open in mini app' button under the /my_bookings reply."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Все записи в Mini App",  # noqa: RUF001
                    web_app=WebAppInfo(url=f"{mini_app_url.rstrip('/')}/my-bookings"),
                )
            ]
        ]
    )


def staff_cabinet_keyboard(mini_app_url: str) -> InlineKeyboardMarkup:
    """Single WebApp button opening /me in the Mini App."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть кабинет",
                    web_app=WebAppInfo(url=f"{mini_app_url.rstrip('/')}/me"),
                )
            ]
        ]
    )
