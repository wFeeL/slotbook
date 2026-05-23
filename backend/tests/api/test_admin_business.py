import pytest

from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_get_business_returns_singleton(
    client, business, admin_user, settings
) -> None:
    response = await client.get(
        "/api/v1/admin/business",
        headers=auth_headers(admin_user, settings),
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == business.id
    assert data["name"] == business.name
    assert data["timezone"] == business.timezone
    assert data["booking_buffer_minutes"] == business.booking_buffer_minutes
    assert data["min_cancellation_hours"] == business.min_cancellation_hours
    assert data["slot_step_minutes"] == business.slot_step_minutes


@pytest.mark.asyncio
async def test_patch_business_updates_fields(
    client, db_session, business, admin_user, settings
) -> None:
    response = await client.patch(
        "/api/v1/admin/business",
        json={"name": "New Name", "booking_buffer_minutes": 15},
        headers=auth_headers(admin_user, settings),
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "New Name"
    assert data["booking_buffer_minutes"] == 15
    # untouched fields preserved
    assert data["timezone"] == business.timezone
    assert data["slot_step_minutes"] == business.slot_step_minutes

    await db_session.refresh(business)
    assert business.name == "New Name"
    assert business.booking_buffer_minutes == 15


@pytest.mark.asyncio
async def test_patch_business_rejects_bad_timezone(
    client, business, admin_user, settings
) -> None:
    response = await client.patch(
        "/api/v1/admin/business",
        json={"timezone": "Mars/Crater"},
        headers=auth_headers(admin_user, settings),
    )
    assert response.status_code == 422, response.text
