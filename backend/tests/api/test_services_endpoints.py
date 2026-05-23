import pytest

from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_list_services_returns_active_only(
    client, db_session, business, branch, client_user, settings
) -> None:
    from app.db.models.service import Service

    db_session.add_all(
        [
            Service(
                business_id=business.id,
                branch_id=branch.id,
                title="A",
                duration_minutes=30,
                sort_order=2,
                is_active=True,
            ),
            Service(
                business_id=business.id,
                branch_id=branch.id,
                title="B",
                duration_minutes=60,
                sort_order=1,
                is_active=True,
            ),
            Service(
                business_id=business.id,
                branch_id=branch.id,
                title="X",
                duration_minutes=60,
                sort_order=0,
                is_active=False,
            ),
        ]
    )
    await db_session.commit()

    response = await client.get("/api/v1/services", headers=auth_headers(client_user, settings))
    assert response.status_code == 200
    titles = [s["title"] for s in response.json()]
    assert titles == ["B", "A"]


@pytest.mark.asyncio
async def test_list_services_requires_auth(client) -> None:
    response = await client.get("/api/v1/services")
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "invalid_token"
