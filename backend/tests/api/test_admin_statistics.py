"""API tests for the admin statistics endpoint."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.db.enums import BookingSource, BookingStatus
from app.db.models.booking import Booking
from app.db.models.service import Service
from app.db.models.staff import StaffMember
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_statistics_empty_business_returns_zero_values(
    client, business, admin_user, settings
) -> None:
    resp = await client.get(
        "/api/v1/admin/statistics",
        headers=auth_headers(admin_user, settings),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["period"] == "30d"
    assert data["revenue"] == "0"
    assert data["total_bookings"] == 0
    assert data["completed_count"] == 0
    assert data["no_show_count"] == 0
    assert data["cancellation_count"] == 0
    assert data["cancellation_rate"] == 0.0
    assert data["top_services"] == []
    assert data["top_staff"] == []
    assert data["daily_volume"] == []


@pytest.mark.asyncio
async def test_statistics_aggregates_seeded_bookings(
    client, db_session, business, client_user, admin_user, settings
) -> None:
    svc = Service(
        business_id=business.id,
        title="Haircut",
        duration_minutes=60,
        price=Decimal("100.00"),
    )
    staff = StaffMember(business_id=business.id, name="Alice")
    db_session.add_all([svc, staff])
    await db_session.flush()

    base = datetime.now(UTC) - timedelta(days=1)
    bookings = [
        Booking(
            business_id=business.id,
            client_id=client_user.id,
            staff_id=staff.id,
            service_id=svc.id,
            starts_at=base + timedelta(hours=1),
            ends_at=base + timedelta(hours=2),
            status=BookingStatus.COMPLETED,
            source=BookingSource.MINI_APP,
        ),
        Booking(
            business_id=business.id,
            client_id=client_user.id,
            staff_id=staff.id,
            service_id=svc.id,
            starts_at=base + timedelta(hours=3),
            ends_at=base + timedelta(hours=4),
            status=BookingStatus.CANCELLED_BY_CLIENT,
            source=BookingSource.MINI_APP,
        ),
        Booking(
            business_id=business.id,
            client_id=client_user.id,
            staff_id=staff.id,
            service_id=svc.id,
            starts_at=base + timedelta(hours=5),
            ends_at=base + timedelta(hours=6),
            status=BookingStatus.NO_SHOW,
            source=BookingSource.MINI_APP,
        ),
    ]
    db_session.add_all(bookings)
    await db_session.commit()

    resp = await client.get(
        "/api/v1/admin/statistics?period=7d",
        headers=auth_headers(admin_user, settings),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["period"] == "7d"
    assert data["total_bookings"] == 3
    assert data["completed_count"] == 1
    assert data["no_show_count"] == 1
    assert data["cancellation_count"] == 1
    assert data["cancellation_rate"] == pytest.approx(1 / 3, rel=1e-2)
    assert data["revenue"] == "100.00"

    assert len(data["top_services"]) == 1
    assert data["top_services"][0]["service_id"] == svc.id
    assert data["top_services"][0]["service_title"] == "Haircut"
    assert data["top_services"][0]["completed_count"] == 1
    assert data["top_services"][0]["revenue"] == "100.00"

    assert len(data["top_staff"]) == 1
    assert data["top_staff"][0]["staff_id"] == staff.id
    assert data["top_staff"][0]["staff_name"] == "Alice"
    assert data["top_staff"][0]["completed_count"] == 1

    assert len(data["daily_volume"]) >= 1
    total_in_days = sum(row["bookings_count"] for row in data["daily_volume"])
    assert total_in_days == 3


@pytest.mark.asyncio
async def test_statistics_filter_by_staff_id(
    client, db_session, business, client_user, admin_user, settings
) -> None:
    svc = Service(
        business_id=business.id,
        title="Trim",
        duration_minutes=30,
        price=Decimal("50.00"),
    )
    staff_a = StaffMember(business_id=business.id, name="Alice")
    staff_b = StaffMember(business_id=business.id, name="Bob")
    db_session.add_all([svc, staff_a, staff_b])
    await db_session.flush()

    base = datetime.now(UTC) - timedelta(days=1)
    db_session.add_all(
        [
            Booking(
                business_id=business.id,
                client_id=client_user.id,
                staff_id=staff_a.id,
                service_id=svc.id,
                starts_at=base + timedelta(hours=1),
                ends_at=base + timedelta(hours=2),
                status=BookingStatus.COMPLETED,
                source=BookingSource.MINI_APP,
            ),
            Booking(
                business_id=business.id,
                client_id=client_user.id,
                staff_id=staff_b.id,
                service_id=svc.id,
                starts_at=base + timedelta(hours=3),
                ends_at=base + timedelta(hours=4),
                status=BookingStatus.COMPLETED,
                source=BookingSource.MINI_APP,
            ),
            Booking(
                business_id=business.id,
                client_id=client_user.id,
                staff_id=staff_b.id,
                service_id=svc.id,
                starts_at=base + timedelta(hours=5),
                ends_at=base + timedelta(hours=6),
                status=BookingStatus.COMPLETED,
                source=BookingSource.MINI_APP,
            ),
        ]
    )
    await db_session.commit()

    resp_all = await client.get(
        "/api/v1/admin/statistics?period=7d",
        headers=auth_headers(admin_user, settings),
    )
    assert resp_all.status_code == 200, resp_all.text
    assert resp_all.json()["total_bookings"] == 3
    assert resp_all.json()["completed_count"] == 3

    resp_b = await client.get(
        f"/api/v1/admin/statistics?period=7d&staff_id={staff_b.id}",
        headers=auth_headers(admin_user, settings),
    )
    assert resp_b.status_code == 200, resp_b.text
    data_b = resp_b.json()
    assert data_b["total_bookings"] == 2
    assert data_b["completed_count"] == 2
    assert len(data_b["top_staff"]) == 1
    assert data_b["top_staff"][0]["staff_id"] == staff_b.id


@pytest.mark.asyncio
async def test_export_bookings_csv_returns_header_and_rows(
    client, db_session, business, client_user, admin_user, settings
) -> None:
    svc = Service(
        business_id=business.id,
        title="Spa",
        duration_minutes=60,
        price=Decimal("200.00"),
    )
    staff = StaffMember(business_id=business.id, name="Carol")
    db_session.add_all([svc, staff])
    await db_session.flush()

    base = datetime.now(UTC) - timedelta(days=1)
    db_session.add(
        Booking(
            business_id=business.id,
            client_id=client_user.id,
            staff_id=staff.id,
            service_id=svc.id,
            starts_at=base + timedelta(hours=1),
            ends_at=base + timedelta(hours=2),
            status=BookingStatus.COMPLETED,
            source=BookingSource.MINI_APP,
            client_comment="please call",
        )
    )
    await db_session.commit()

    resp = await client.get(
        "/api/v1/admin/exports/bookings.csv",
        headers=auth_headers(admin_user, settings),
    )
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("text/csv")
    assert "attachment" in resp.headers["content-disposition"]

    text = resp.text
    lines = [line for line in text.splitlines() if line.strip()]
    # Header + at least one body row
    assert len(lines) >= 2
    header = lines[0].split(",")
    assert "id" in header
    assert "status" in header
    assert "service_title" in header
    # Body row contains seeded data
    body_blob = "\n".join(lines[1:])
    assert "Spa" in body_blob
    assert "Carol" in body_blob


@pytest.mark.asyncio
async def test_export_bookings_xlsx_returns_correct_mime(
    client, db_session, business, client_user, admin_user, settings
) -> None:
    svc = Service(
        business_id=business.id,
        title="Mani",
        duration_minutes=30,
        price=Decimal("75.00"),
    )
    staff = StaffMember(business_id=business.id, name="Dora")
    db_session.add_all([svc, staff])
    await db_session.flush()

    base = datetime.now(UTC) - timedelta(days=1)
    db_session.add(
        Booking(
            business_id=business.id,
            client_id=client_user.id,
            staff_id=staff.id,
            service_id=svc.id,
            starts_at=base + timedelta(hours=1),
            ends_at=base + timedelta(hours=2),
            status=BookingStatus.COMPLETED,
            source=BookingSource.MINI_APP,
        )
    )
    await db_session.commit()

    resp = await client.get(
        "/api/v1/admin/exports/bookings.xlsx",
        headers=auth_headers(admin_user, settings),
    )
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert "attachment" in resp.headers["content-disposition"]
    # XLSX files are ZIPs and start with PK signature
    assert resp.content[:2] == b"PK"
    assert len(resp.content) > 0
