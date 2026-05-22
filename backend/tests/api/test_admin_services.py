import pytest

from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_admin_create_service(client, business, admin_user, settings) -> None:
    response = await client.post(
        "/api/v1/admin/services",
        json={"title": "Стрижка", "duration_minutes": 60, "price": "1500.00"},
        headers=auth_headers(admin_user, settings),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Стрижка"
    assert body["duration_minutes"] == 60
    assert body["is_active"] is True


@pytest.mark.asyncio
async def test_admin_create_service_accepts_superadmin(
    client, business, superadmin_user, settings
) -> None:
    response = await client.post(
        "/api/v1/admin/services",
        json={"title": "SuperAdminService", "duration_minutes": 45},
        headers=auth_headers(superadmin_user, settings),
    )
    assert response.status_code == 201, (
        f"Expected 201 for SUPERADMIN, got {response.status_code}: {response.json()}"
    )
    assert response.json()["title"] == "SuperAdminService"


@pytest.mark.asyncio
async def test_admin_create_service_rejects_client(client, business, client_user, settings) -> None:
    response = await client.post(
        "/api/v1/admin/services",
        json={"title": "X", "duration_minutes": 30},
        headers=auth_headers(client_user, settings),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_update_then_soft_delete(client, business, admin_user, settings) -> None:
    create = await client.post(
        "/api/v1/admin/services",
        json={"title": "Tmp", "duration_minutes": 30},
        headers=auth_headers(admin_user, settings),
    )
    sid = create.json()["id"]

    patch = await client.patch(
        f"/api/v1/admin/services/{sid}",
        json={"title": "Renamed"},
        headers=auth_headers(admin_user, settings),
    )
    assert patch.status_code == 200
    assert patch.json()["title"] == "Renamed"

    delete = await client.delete(
        f"/api/v1/admin/services/{sid}",
        headers=auth_headers(admin_user, settings),
    )
    assert delete.status_code == 204

    # Soft-deleted: should not appear in active list
    active = await client.get("/api/v1/services", headers=auth_headers(admin_user, settings))
    assert sid not in [s["id"] for s in active.json()]
