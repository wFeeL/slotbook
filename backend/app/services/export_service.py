from __future__ import annotations

import csv
import io
from collections.abc import Sequence
from datetime import UTC, date, datetime

from sqlalchemy import Row, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.booking import Booking
from app.db.models.service import Service
from app.db.models.staff import StaffMember
from app.db.models.user import User

COLUMNS = [
    "id",
    "created_at",
    "starts_at",
    "ends_at",
    "status",
    "client_telegram_id",
    "client_first_name",
    "staff_name",
    "service_title",
    "price",
    "client_comment",
    "admin_comment",
]


async def _rows(
    session: AsyncSession,
    business_id: int,
    date_from: date | None,
    date_to: date | None,
    staff_id: int | None,
) -> Sequence[Row]:
    stmt = (
        select(
            Booking.id,
            Booking.created_at,
            Booking.starts_at,
            Booking.ends_at,
            Booking.status,
            User.telegram_id,
            User.first_name,
            StaffMember.name,
            Service.title,
            Service.price,
            Booking.client_comment,
            Booking.admin_comment,
        )
        .select_from(Booking)
        .join(User, User.id == Booking.client_id)
        .join(StaffMember, StaffMember.id == Booking.staff_id)
        .join(Service, Service.id == Booking.service_id)
        .where(Booking.business_id == business_id)
        .order_by(Booking.starts_at)
    )
    if date_from is not None:
        stmt = stmt.where(
            Booking.starts_at >= datetime.combine(date_from, datetime.min.time(), UTC)
        )
    if date_to is not None:
        stmt = stmt.where(
            Booking.starts_at < datetime.combine(date_to, datetime.max.time(), UTC)
        )
    if staff_id is not None:
        stmt = stmt.where(Booking.staff_id == staff_id)
    return (await session.execute(stmt)).all()


async def to_csv(
    session: AsyncSession,
    business_id: int,
    date_from: date | None,
    date_to: date | None,
    staff_id: int | None,
) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(COLUMNS)
    for row in await _rows(session, business_id, date_from, date_to, staff_id):
        writer.writerow([str(v) if v is not None else "" for v in row])
    # Prepend UTF-8 BOM so Excel / Numbers on macOS correctly detect Cyrillic.
    return "﻿" + buf.getvalue()


async def to_xlsx(
    session: AsyncSession,
    business_id: int,
    date_from: date | None,
    date_to: date | None,
    staff_id: int | None,
) -> bytes:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Bookings"
    ws.append(COLUMNS)
    for row in await _rows(session, business_id, date_from, date_to, staff_id):
        ws.append(
            [
                v.isoformat()
                if hasattr(v, "isoformat")
                else (str(v) if v is not None else "")
                for v in row
            ]
        )
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()
