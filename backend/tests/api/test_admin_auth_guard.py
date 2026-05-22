"""Parameterised tests proving every admin route returns 403 for a client-role JWT.

If any route returns something other than 403, that route has a guard problem
(missing AdminUser dependency or wrong dependency injected).
"""

from __future__ import annotations

import pytest

from tests.conftest import auth_headers


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,path,body",
    [
        ("POST", "/api/v1/admin/services", {"title": "X", "duration_minutes": 30}),
        ("PATCH", "/api/v1/admin/services/1", {"title": "Y"}),
        ("DELETE", "/api/v1/admin/services/1", None),
        ("POST", "/api/v1/admin/staff", {"name": "Z"}),
        ("PATCH", "/api/v1/admin/staff/1", {"name": "W"}),
        ("DELETE", "/api/v1/admin/staff/1", None),
        ("PUT", "/api/v1/admin/staff/1/services", {"service_ids": []}),
        ("GET", "/api/v1/admin/staff/1/working-hours", None),
        ("PUT", "/api/v1/admin/staff/1/working-hours", {"entries": []}),
        (
            "POST",
            "/api/v1/admin/staff/1/exceptions",
            {"date": "2026-12-31", "type": "day_off"},
        ),
        ("GET", "/api/v1/admin/bookings", None),
        ("PATCH", "/api/v1/admin/bookings/1", {"status": "completed"}),
        (
            "POST",
            "/api/v1/admin/bookings",
            {
                "client_telegram_id": 1,
                "service_id": 1,
                "staff_id": 1,
                "starts_at": "2030-01-01T12:00:00+00:00",
            },
        ),
        ("POST", "/api/v1/admin/bookings/1/cancel", None),
        ("GET", "/api/v1/admin/dashboard", None),
    ],
)
async def test_admin_routes_reject_client_role(
    client, client_user, settings, method: str, path: str, body: dict | None
) -> None:
    headers = auth_headers(client_user, settings)
    if method == "GET":
        response = await client.get(path, headers=headers)
    elif method == "POST":
        response = await client.post(path, json=body or {}, headers=headers)
    elif method == "PATCH":
        response = await client.patch(path, json=body or {}, headers=headers)
    elif method == "PUT":
        response = await client.put(path, json=body or {}, headers=headers)
    elif method == "DELETE":
        response = await client.delete(path, headers=headers)
    else:
        raise ValueError(f"Unexpected method: {method}")

    assert response.status_code == 403, (
        f"{method} {path} returned {response.status_code}, expected 403"
    )
    assert response.json()["detail"]["code"] == "forbidden"
