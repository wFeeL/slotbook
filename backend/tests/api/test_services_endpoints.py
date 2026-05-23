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


@pytest.mark.asyncio
async def test_list_services_filters_by_branch_id(
    client, db_session, business, branch, client_user, settings
) -> None:
    from app.db.models.branch import Branch
    from app.db.models.service import Service

    second_branch = Branch(
        business_id=business.id, name="Second", timezone=business.timezone, sort_order=1
    )
    db_session.add(second_branch)
    await db_session.commit()
    await db_session.refresh(second_branch)

    db_session.add_all(
        [
            Service(
                business_id=business.id,
                branch_id=branch.id,
                title="A1",
                duration_minutes=30,
                is_active=True,
            ),
            Service(
                business_id=business.id,
                branch_id=branch.id,
                title="A2",
                duration_minutes=30,
                is_active=True,
            ),
            Service(
                business_id=business.id,
                branch_id=second_branch.id,
                title="B1",
                duration_minutes=30,
                is_active=True,
            ),
            Service(
                business_id=business.id,
                branch_id=second_branch.id,
                title="B2",
                duration_minutes=30,
                is_active=True,
            ),
        ]
    )
    await db_session.commit()

    headers = auth_headers(client_user, settings)
    resp_a = await client.get(f"/api/v1/services?branch_id={branch.id}", headers=headers)
    assert resp_a.status_code == 200
    titles_a = sorted(s["title"] for s in resp_a.json())
    assert titles_a == ["A1", "A2"]

    resp_b = await client.get(
        f"/api/v1/services?branch_id={second_branch.id}", headers=headers
    )
    assert resp_b.status_code == 200
    titles_b = sorted(s["title"] for s in resp_b.json())
    assert titles_b == ["B1", "B2"]
