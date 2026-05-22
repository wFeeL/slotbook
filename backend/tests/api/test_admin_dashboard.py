"""API tests for the admin dashboard endpoint."""

from __future__ import annotations

import pytest

from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_dashboard_returns_zero_counts_for_empty_db(
    client, business, admin_user, settings
) -> None:  # type: ignore[no-untyped-def]
    """With no bookings, all dashboard counts should be 0."""
    resp = await client.get(
        "/api/v1/admin/dashboard",
        headers=auth_headers(admin_user, settings),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"counts": {"today": 0, "this_week": 0, "no_show_30d": 0}}
