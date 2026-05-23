from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import structlog
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import (
    CancellationTooLate,
    CannotCancelInCurrentStatus,
    Forbidden,
    NotFound,
    ServiceInactive,
    SlotAlreadyTaken,
    SlotInPast,
    SlotOutsideWorkingHours,
    StaffDoesNotOfferService,
    StaffInactive,
)
from app.core.time import local_date_bounds_utc
from app.db.enums import (
    BookingSource,
    BookingStatus,
    NotificationStatus,
    NotificationType,
    UserRole,
)
from app.db.models.booking import Booking
from app.db.models.business import Business
from app.db.models.notification import Notification
from app.db.models.user import User
from app.db.repositories.audit import AuditRepo
from app.db.repositories.bookings import BookingsRepo
from app.db.repositories.notifications import NotificationsRepo
from app.db.repositories.schedules import ScheduleExceptionsRepo, WorkingHoursRepo
from app.db.repositories.services import ServicesRepo
from app.db.repositories.staff import StaffRepo
from app.services.slot_service import (
    BusyInterval,
    ExceptionEntry,
    Slot,
    WorkingInterval,
    calculate_available_slots,
)

logger = structlog.get_logger(__name__)


class BookingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_slot_conflict(exc: IntegrityError) -> bool:
        """Return True if the IntegrityError is a slot-conflict on the booking unique index or the EXCLUDE constraint."""
        exc_str = str(exc)
        if "bookings_active_by_staff" in exc_str or "bookings_no_overlap" in exc_str:
            return True
        if exc.orig is not None:
            if "bookings_active_by_staff" in str(exc.orig) or "bookings_no_overlap" in str(
                exc.orig
            ):
                return True
            # asyncpg UniqueViolationError / ExclusionViolationError exposes constraint_name
            constraint_name = getattr(exc.orig, "constraint_name", None)
            if constraint_name in ("bookings_active_by_staff", "bookings_no_overlap"):
                return True
        return False

    async def _admin_user_ids(self, _business_id: int) -> list[int]:
        """All admin (and superadmin) users system-wide.

        Multi-tenant scoping will be added later. SUPERADMINs must receive
        admin-targeted notifications too — otherwise they miss BOOKING_CREATED_ADMIN
        and BOOKING_CANCELLED_ADMIN events for bookings they ought to oversee.
        """
        stmt = select(User.id).where(User.role.in_([UserRole.ADMIN, UserRole.SUPERADMIN]))
        return list((await self.session.execute(stmt)).scalars().all())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def create_booking(
        self,
        *,
        business: Business,
        actor_user_id: int,
        client_id: int,
        staff_id: int,
        service_id: int,
        starts_at: datetime,
        client_comment: str | None = None,
        source: BookingSource = BookingSource.MINI_APP,
        now_utc: datetime | None = None,
    ) -> Booking:
        now = now_utc or datetime.now(UTC)

        # 1. starts_at must be timezone-aware; reject naive datetimes
        if starts_at.tzinfo is None:
            raise SlotInPast("starts_at must be timezone-aware")

        # Normalise to UTC
        starts_at_utc = starts_at.astimezone(UTC)

        # 2. Reject past slots
        if starts_at_utc < now:
            raise SlotInPast()

        # 3. Load service — 404 if missing or different business
        service = await ServicesRepo(self.session).get(service_id)
        if service is None or service.business_id != business.id:
            raise NotFound("Service not found")
        if not service.is_active:
            raise ServiceInactive()

        # 4. Load staff — 404 if missing or different business
        staff = await StaffRepo(self.session).get(staff_id)
        if staff is None or staff.business_id != business.id:
            raise NotFound("Staff member not found")
        if not staff.is_active:
            raise StaffInactive()

        # 5. Verify staff offers this service
        if not await StaffRepo(self.session).offers_service(staff_id, service_id):
            raise StaffDoesNotOfferService()

        # 5b. Cross-branch consistency
        if service.branch_id != staff.branch_id:
            raise NotFound("Service and staff belong to different branches")
        booking_branch_id = service.branch_id

        # 6. Calculate ends_at
        ends_at_utc = starts_at_utc + timedelta(minutes=service.duration_minutes)

        # 7. RACE-CRITICAL: lock overlapping rows
        overlapping = await BookingsRepo(self.session).find_overlapping_for_update(
            staff_id, starts_at_utc, ends_at_utc
        )
        if overlapping:
            raise SlotAlreadyTaken()

        # 8. Validate the slot is within working hours using real business
        #    slot_step_minutes and booking_buffer_minutes so we reject bookings
        #    at non-step times and enforce the buffer between bookings.
        target_date = starts_at_utc.astimezone(ZoneInfo(business.timezone)).date()
        day_start_utc, day_end_utc = local_date_bounds_utc(target_date, business.timezone)
        existing = await BookingsRepo(self.session).list_active_for_staff_range(
            staff_id, day_start_utc, day_end_utc
        )
        busy = [BusyInterval(start=b.starts_at, end=b.ends_at) for b in existing]

        wh_rows = await WorkingHoursRepo(self.session).list_for_staff_weekday(
            staff_id, target_date.weekday()
        )
        working_intervals = [WorkingInterval(r.start_time, r.end_time) for r in wh_rows]

        exc_rows = await ScheduleExceptionsRepo(self.session).list_for_staff_date(
            staff_id, target_date
        )
        exceptions = [
            ExceptionEntry(type=e.type, start=e.start_time, end=e.end_time) for e in exc_rows
        ]

        candidate_slots: list[Slot] = calculate_available_slots(
            target_date=target_date,
            business_timezone=business.timezone,
            service_duration_minutes=service.duration_minutes,
            slot_step_minutes=business.slot_step_minutes,
            buffer_minutes=business.booking_buffer_minutes,
            working_hours=working_intervals,
            exceptions=exceptions,
            bookings=busy,
            now_utc=now,
        )
        if not any(s.starts_at_utc == starts_at_utc for s in candidate_slots):
            raise SlotOutsideWorkingHours()

        # 9. Insert the booking
        booking = Booking(
            business_id=business.id,
            branch_id=booking_branch_id,
            client_id=client_id,
            staff_id=staff_id,
            service_id=service_id,
            starts_at=starts_at_utc,
            ends_at=ends_at_utc,
            status=BookingStatus.CONFIRMED,
            client_comment=client_comment,
            source=source,
        )
        BookingsRepo(self.session).add(booking)
        try:
            await self.session.flush()  # get booking.id — unique violation may surface here
        except IntegrityError as exc:
            await self.session.rollback()
            if self._is_slot_conflict(exc):
                raise SlotAlreadyTaken() from exc
            raise

        # 10. Create pending notifications
        notif_repo = NotificationsRepo(self.session)
        notif_repo.add(
            Notification(
                booking_id=booking.id,
                user_id=client_id,
                notification_type=NotificationType.BOOKING_CREATED_CLIENT,
                notification_status=NotificationStatus.PENDING,
            )
        )
        admin_ids = await self._admin_user_ids(business.id)
        for admin_id in admin_ids:
            notif_repo.add(
                Notification(
                    booking_id=booking.id,
                    user_id=admin_id,
                    notification_type=NotificationType.BOOKING_CREATED_ADMIN,
                    notification_status=NotificationStatus.PENDING,
                )
            )

        # Enqueue reminder notifications for client (only if T-24h / T-2h is in the future)
        reminder_24h_at = starts_at_utc - timedelta(hours=24)
        reminder_2h_at = starts_at_utc - timedelta(hours=2)
        if reminder_24h_at > now:
            notif_repo.add(
                Notification(
                    booking_id=booking.id,
                    user_id=client_id,
                    notification_type=NotificationType.REMINDER_24H,
                    notification_status=NotificationStatus.PENDING,
                    scheduled_at=reminder_24h_at,
                )
            )
        if reminder_2h_at > now:
            notif_repo.add(
                Notification(
                    booking_id=booking.id,
                    user_id=client_id,
                    notification_type=NotificationType.REMINDER_2H,
                    notification_status=NotificationStatus.PENDING,
                    scheduled_at=reminder_2h_at,
                )
            )

        # 11. Insert audit log
        AuditRepo(self.session).log(
            actor_user_id=actor_user_id,
            action="booking_created",
            entity_type="booking",
            entity_id=booking.id,
            metadata={"staff_id": staff_id, "service_id": service_id, "source": source.value},
        )

        # 12. Commit — locks released, booking persisted atomically.
        # Catch unique violation on (staff_id, starts_at) partial index — this handles
        # the INSERT race condition where two concurrent transactions both passed the
        # SELECT FOR UPDATE check (no existing rows to lock) and both attempted to INSERT.
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            if self._is_slot_conflict(exc):
                raise SlotAlreadyTaken() from exc
            raise
        await self.session.refresh(booking)

        logger.info(
            "booking.created",
            booking_id=booking.id,
            client_id=client_id,
            staff_id=staff_id,
            service_id=service_id,
        )
        return booking

    async def cancel_booking(
        self,
        *,
        business: Business,
        actor_user_id: int,
        actor_role: UserRole,
        booking_id: int,
        now_utc: datetime | None = None,
    ) -> Booking:
        now = now_utc or datetime.now(UTC)
        now = now.replace(tzinfo=UTC) if now.tzinfo is None else now.astimezone(UTC)

        is_admin = actor_role in {UserRole.ADMIN, UserRole.SUPERADMIN}

        # 2. Load booking — 404 if missing or wrong business
        booking = await BookingsRepo(self.session).get(booking_id)
        if booking is None or booking.business_id != business.id:
            raise NotFound("Booking not found")

        # 3. Ownership check
        if not is_admin and booking.client_id != actor_user_id:
            raise Forbidden("You can only cancel your own bookings")

        # 4. Status check
        cancellable = {BookingStatus.PENDING, BookingStatus.CONFIRMED}
        if booking.status not in cancellable:
            raise CannotCancelInCurrentStatus()

        # 5. Time limit check (clients only)
        if not is_admin:
            hours_left = (booking.starts_at - now).total_seconds() / 3600.0
            if hours_left < business.min_cancellation_hours:
                raise CancellationTooLate()

        # 6. Update booking status
        previous_status = booking.status.value
        booking.status = (
            BookingStatus.CANCELLED_BY_ADMIN if is_admin else BookingStatus.CANCELLED_BY_CLIENT
        )
        booking.cancelled_at = now

        # 7. Notifications
        notif_repo = NotificationsRepo(self.session)
        notif_repo.add(
            Notification(
                booking_id=booking.id,
                user_id=booking.client_id,
                notification_type=NotificationType.BOOKING_CANCELLED_CLIENT,
                notification_status=NotificationStatus.PENDING,
            )
        )
        admin_ids = await self._admin_user_ids(business.id)
        for admin_id in admin_ids:
            notif_repo.add(
                Notification(
                    booking_id=booking.id,
                    user_id=admin_id,
                    notification_type=NotificationType.BOOKING_CANCELLED_ADMIN,
                    notification_status=NotificationStatus.PENDING,
                )
            )

        # Purge still-pending reminders so we don't send them after cancellation
        await notif_repo.delete_pending_reminders_for_booking(booking.id)

        # 8. Audit log
        metadata: dict[str, Any] = {
            "cancelled_by_role": actor_role.value,
            "previous_status": previous_status,
        }
        AuditRepo(self.session).log(
            actor_user_id=actor_user_id,
            action="booking_cancelled",
            entity_type="booking",
            entity_id=booking.id,
            metadata=metadata,
        )

        # 9. Commit
        await self.session.commit()
        await self.session.refresh(booking)

        logger.info(
            "booking.cancelled",
            booking_id=booking.id,
            actor_user_id=actor_user_id,
            is_admin=is_admin,
        )
        return booking

    async def reschedule_booking(
        self,
        *,
        business: Business,
        actor_user_id: int,
        actor_role: UserRole,
        booking_id: int,
        new_starts_at: datetime,
        now_utc: datetime | None = None,
    ) -> Booking:
        now = now_utc or datetime.now(UTC)
        if new_starts_at.tzinfo is None:
            raise SlotInPast("new_starts_at must be timezone-aware")
        new_starts_at_utc = new_starts_at.astimezone(UTC)

        is_admin = actor_role in {UserRole.ADMIN, UserRole.SUPERADMIN}

        booking = await BookingsRepo(self.session).get(booking_id)
        if booking is None or booking.business_id != business.id:
            raise NotFound("Booking not found")

        if not is_admin and booking.client_id != actor_user_id:
            raise Forbidden("You can only reschedule your own bookings")

        if booking.status not in {BookingStatus.PENDING, BookingStatus.CONFIRMED}:
            raise CannotCancelInCurrentStatus()

        # Time-limit guard (clients only) — same as cancel
        if not is_admin:
            hours_left = (booking.starts_at - now).total_seconds() / 3600.0
            if hours_left < business.min_cancellation_hours:
                raise CancellationTooLate()

        # Reject past slots
        if new_starts_at_utc < now:
            raise SlotInPast()

        # Recompute ends_at using the existing service's duration
        service = await ServicesRepo(self.session).get(booking.service_id)
        if service is None:
            raise NotFound("Service not found")
        new_ends_at_utc = new_starts_at_utc + timedelta(minutes=service.duration_minutes)

        # Lock overlapping rows (excluding self via id != booking.id)
        overlapping = await BookingsRepo(self.session).find_overlapping_for_update(
            booking.staff_id,
            new_starts_at_utc,
            new_ends_at_utc,
            exclude_id=booking.id,
        )
        if overlapping:
            raise SlotAlreadyTaken()

        # Working-hours validation reuse — same pattern as create_booking
        target_date = new_starts_at_utc.astimezone(ZoneInfo(business.timezone)).date()
        day_start_utc, day_end_utc = local_date_bounds_utc(target_date, business.timezone)
        existing = await BookingsRepo(self.session).list_active_for_staff_range(
            booking.staff_id, day_start_utc, day_end_utc
        )
        # Exclude self from busy list
        busy = [
            BusyInterval(start=b.starts_at, end=b.ends_at)
            for b in existing
            if b.id != booking.id
        ]

        wh_rows = await WorkingHoursRepo(self.session).list_for_staff_weekday(
            booking.staff_id, target_date.weekday()
        )
        working_intervals = [WorkingInterval(r.start_time, r.end_time) for r in wh_rows]

        exc_rows = await ScheduleExceptionsRepo(self.session).list_for_staff_date(
            booking.staff_id, target_date
        )
        exceptions = [
            ExceptionEntry(type=e.type, start=e.start_time, end=e.end_time) for e in exc_rows
        ]

        candidate_slots = calculate_available_slots(
            target_date=target_date,
            business_timezone=business.timezone,
            service_duration_minutes=service.duration_minutes,
            slot_step_minutes=business.slot_step_minutes,
            buffer_minutes=business.booking_buffer_minutes,
            working_hours=working_intervals,
            exceptions=exceptions,
            bookings=busy,
            now_utc=now,
        )
        if not any(s.starts_at_utc == new_starts_at_utc for s in candidate_slots):
            raise SlotOutsideWorkingHours()

        # All checks passed — update the row
        old_starts_at = booking.starts_at
        booking.starts_at = new_starts_at_utc
        booking.ends_at = new_ends_at_utc
        booking.rescheduled_at = now

        # Delete pending reminders for this booking
        notif_repo = NotificationsRepo(self.session)
        await notif_repo.delete_pending_reminders_for_booking(booking.id)

        # Enqueue fresh reminders (only if future)
        reminder_24h_at = new_starts_at_utc - timedelta(hours=24)
        reminder_2h_at = new_starts_at_utc - timedelta(hours=2)
        if reminder_24h_at > now:
            notif_repo.add(
                Notification(
                    booking_id=booking.id,
                    user_id=booking.client_id,
                    notification_type=NotificationType.REMINDER_24H,
                    notification_status=NotificationStatus.PENDING,
                    scheduled_at=reminder_24h_at,
                )
            )
        if reminder_2h_at > now:
            notif_repo.add(
                Notification(
                    booking_id=booking.id,
                    user_id=booking.client_id,
                    notification_type=NotificationType.REMINDER_2H,
                    notification_status=NotificationStatus.PENDING,
                    scheduled_at=reminder_2h_at,
                )
            )

        # Immediate notifications (client + admins)
        notif_repo.add(
            Notification(
                booking_id=booking.id,
                user_id=booking.client_id,
                notification_type=NotificationType.BOOKING_RESCHEDULED_CLIENT,
                notification_status=NotificationStatus.PENDING,
            )
        )
        admin_ids = await self._admin_user_ids(business.id)
        for admin_id in admin_ids:
            notif_repo.add(
                Notification(
                    booking_id=booking.id,
                    user_id=admin_id,
                    notification_type=NotificationType.BOOKING_RESCHEDULED_ADMIN,
                    notification_status=NotificationStatus.PENDING,
                )
            )

        AuditRepo(self.session).log(
            actor_user_id=actor_user_id,
            action="booking_rescheduled",
            entity_type="booking",
            entity_id=booking.id,
            metadata={
                "old_starts_at": old_starts_at.isoformat(),
                "new_starts_at": new_starts_at_utc.isoformat(),
                "actor_role": actor_role.value,
            },
        )

        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            if self._is_slot_conflict(exc):
                raise SlotAlreadyTaken() from exc
            raise
        await self.session.refresh(booking)

        logger.info(
            "booking.rescheduled",
            booking_id=booking.id,
            old=old_starts_at.isoformat(),
            new=new_starts_at_utc.isoformat(),
        )
        return booking
