from __future__ import annotations

from datetime import date as date_t
from datetime import datetime, time

import sqlalchemy
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    Text,
    Time,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.enums import ScheduleExceptionType


class WorkingHours(Base):
    __tablename__ = "working_hours"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    staff_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("staff_members.id", ondelete="CASCADE"), nullable=False
    )
    weekday: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 0=Mon ... 6=Sun
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint("weekday >= 0 AND weekday <= 6", name="ck_working_hours_weekday"),
        CheckConstraint("end_time > start_time", name="ck_working_hours_end_after_start"),
        Index("ix_working_hours_staff_weekday", "staff_id", "weekday"),
    )


class ScheduleException(Base):
    __tablename__ = "schedule_exceptions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    staff_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("staff_members.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date_t] = mapped_column(Date, nullable=False)
    start_time: Mapped[time | None] = mapped_column(Time)
    end_time: Mapped[time | None] = mapped_column(Time)
    type: Mapped[ScheduleExceptionType] = mapped_column(
        sqlalchemy.Enum(
            ScheduleExceptionType,
            name="schedule_exception_type",
            values_callable=lambda obj: [e.value for e in obj],
            create_type=False,
        ),
        nullable=False,
    )
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (Index("ix_schedule_exceptions_staff_date", "staff_id", "date"),)
