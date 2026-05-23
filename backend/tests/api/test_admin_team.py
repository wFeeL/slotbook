"""API tests for the admin team + invites endpoints."""

from __future__ import annotations

import pytest

from app.db.models.admin_invite import AdminInvite
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_team_returns_only_admin_member_and_no_invites(
    client, business, admin_user, settings
) -> None:
    resp = await client.get(
        "/api/v1/admin/team",
        headers=auth_headers(admin_user, settings),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    # Members include the admin_user fixture (role=admin), but no invites yet.
    assert isinstance(data["members"], list)
    assert any(m["id"] == admin_user.id for m in data["members"])
    assert data["invites"] == []


@pytest.mark.asyncio
async def test_create_invite_returns_url_and_persists(
    client, db_session, business, admin_user, settings
) -> None:
    resp = await client.post(
        "/api/v1/admin/invites",
        json={"role": "admin", "ttl_hours": 24},
        headers=auth_headers(admin_user, settings),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["role"] == "admin"
    assert data["url"].startswith("https://t.me/")
    assert f"start=invite_{data['token']}" in data["url"]

    # Stored row exists.
    row = await db_session.get(AdminInvite, data["id"])
    assert row is not None
    assert row.business_id == business.id
    assert row.token == data["token"]
    assert row.consumed_at is None


@pytest.mark.asyncio
async def test_created_invite_appears_in_team_listing(
    client, business, admin_user, settings
) -> None:
    create = await client.post(
        "/api/v1/admin/invites",
        json={"role": "staff", "ttl_hours": 168},
        headers=auth_headers(admin_user, settings),
    )
    assert create.status_code == 201, create.text
    created = create.json()

    team = await client.get(
        "/api/v1/admin/team",
        headers=auth_headers(admin_user, settings),
    )
    assert team.status_code == 200, team.text
    invites = team.json()["invites"]
    assert any(i["id"] == created["id"] and i["role"] == "staff" for i in invites)


@pytest.mark.asyncio
async def test_revoke_invite_removes_from_active_list(
    client, business, admin_user, settings
) -> None:
    create = await client.post(
        "/api/v1/admin/invites",
        json={"role": "admin", "ttl_hours": 24},
        headers=auth_headers(admin_user, settings),
    )
    invite_id = create.json()["id"]

    delete = await client.delete(
        f"/api/v1/admin/invites/{invite_id}",
        headers=auth_headers(admin_user, settings),
    )
    assert delete.status_code == 204, delete.text

    team = await client.get(
        "/api/v1/admin/team",
        headers=auth_headers(admin_user, settings),
    )
    assert team.status_code == 200, team.text
    assert all(i["id"] != invite_id for i in team.json()["invites"])
