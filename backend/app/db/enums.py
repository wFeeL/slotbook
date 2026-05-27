from enum import StrEnum


class UserRole(StrEnum):
    CLIENT = "client"
    ADMIN = "admin"
    STAFF = "staff"
    SUPERADMIN = "superadmin"


class BookingStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED_BY_CLIENT = "cancelled_by_client"
    CANCELLED_BY_ADMIN = "cancelled_by_admin"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class BookingSource(StrEnum):
    MINI_APP = "mini_app"
    BOT = "bot"
    ADMIN_MANUAL = "admin_manual"


class ScheduleExceptionType(StrEnum):
    DAY_OFF = "day_off"
    EXTRA_WORKING_TIME = "extra_working_time"
    BLOCKED_TIME = "blocked_time"


class NotificationType(StrEnum):
    BOOKING_CREATED_CLIENT = "booking_created_client"
    BOOKING_CREATED_ADMIN = "booking_created_admin"
    BOOKING_CREATED_STAFF = "booking_created_staff"
    REMINDER_24H = "reminder_24h"
    REMINDER_2H = "reminder_2h"
    BOOKING_CANCELLED_CLIENT = "booking_cancelled_client"
    BOOKING_CANCELLED_ADMIN = "booking_cancelled_admin"
    BOOKING_CANCELLED_STAFF = "booking_cancelled_staff"
    BOOKING_RESCHEDULED_CLIENT = "booking_rescheduled_client"
    BOOKING_RESCHEDULED_ADMIN = "booking_rescheduled_admin"
    BOOKING_RESCHEDULED_STAFF = "booking_rescheduled_staff"


class NotificationStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class PhotoOwnerType(StrEnum):
    SERVICE = "service"
    STAFF = "staff"
