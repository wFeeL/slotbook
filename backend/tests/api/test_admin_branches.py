from __future__ import annotations

import pytest

from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_admin_create_branch_returns_201_with_body(
    client, business, admin_user, settings
) -> None:
    response = await client.post(
        "/api/v1/admin/branches",
        json={"name": "Downtown", "address": "Main St 1", "timezone": "Europe/Moscow"},
        headers=auth_headers(admin_user, settings),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["name"] == "Downtown"
    assert body["address"] == "Main St 1"
    assert body["timezone"] == "Europe/Moscow"
    assert body["is_active"] is True
    assert body["sort_order"] == 0


@pytest.mark.asyncio
async def test_admin_list_branches_includes_default_and_new(
    client, business, admin_user, settings
) -> None:
    create = await client.post(
        "/api/v1/admin/branches",
        json={"name": "Second", "timezone": "UTC"},
        headers=auth_headers(admin_user, settings),
    )
    assert create.status_code == 201, create.text

    listing = await client.get(
        "/api/v1/admin/branches",
        headers=auth_headers(admin_user, settings),
    )
    assert listing.status_code == 200, listing.text
    names = sorted(b["name"] for b in listing.json())
    assert "Second" in names
    # Default branch (created by `business` fixture) shares the business name.
    assert business.name in names


@pytest.mark.asyncio
async def test_admin_archive_branch_hides_from_public_list(
    client, business, admin_user, client_user, settings
) -> None:
    create = await client.post(
        "/api/v1/admin/branches",
        json={"name": "Temp", "timezone": "UTC"},
        headers=auth_headers(admin_user, settings),
    )
    branch_id = create.json()["id"]

    archive = await client.delete(
        f"/api/v1/admin/branches/{branch_id}",
        headers=auth_headers(admin_user, settings),
    )
    assert archive.status_code == 204

    public = await client.get(
        "/api/v1/branches",
        headers=auth_headers(client_user, settings),
    )
    assert public.status_code == 200, public.text
    ids = [b["id"] for b in public.json()]
    assert branch_id not in ids


@pytest.mark.asyncio
async def test_admin_create_branch_rejects_bad_timezone(
    client, business, admin_user, settings
) -> None:
    response = await client.post(
        "/api/v1/admin/branches",
        json={"name": "Bad", "timezone": "Not/A/Real/Zone"},
        headers=auth_headers(admin_user, settings),
    )
    assert response.status_code == 422, response.text
