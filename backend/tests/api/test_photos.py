from __future__ import annotations

import pytest

from app.db.enums import PhotoOwnerType
from app.db.models.photo import Photo
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_create_upload_intent_returns_bot_url(
    client, db_session, business, admin_user, settings
) -> None:
    from app.db.models.service import Service
    svc = Service(
        business_id=business.id, branch_id=business._default_branch_id,
        title="X", duration_minutes=30,
    )
    db_session.add(svc)
    await db_session.commit()
    await db_session.refresh(svc)

    res = await client.post(
        "/api/v1/admin/photos/upload-intent",
        json={"owner_type": "service", "owner_id": svc.id},
        headers=auth_headers(admin_user, settings),
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["bot_url"].startswith("https://t.me/")
    assert body["bot_url"].endswith("?start=upload")
    assert "expires_at" in body


@pytest.mark.asyncio
async def test_create_upload_intent_replaces_existing(
    client, db_session, business, admin_user, settings
) -> None:
    from app.db.models.pending_photo_upload import PendingPhotoUpload
    from app.db.models.service import Service
    from sqlalchemy import select

    svc1 = Service(business_id=business.id, branch_id=business._default_branch_id, title="A", duration_minutes=30)
    svc2 = Service(business_id=business.id, branch_id=business._default_branch_id, title="B", duration_minutes=30)
    db_session.add_all([svc1, svc2])
    await db_session.commit()
    await db_session.refresh(svc1)
    await db_session.refresh(svc2)

    for sid in (svc1.id, svc2.id):
        res = await client.post(
            "/api/v1/admin/photos/upload-intent",
            json={"owner_type": "service", "owner_id": sid},
            headers=auth_headers(admin_user, settings),
        )
        assert res.status_code == 201, res.text

    rows = (
        await db_session.execute(
            select(PendingPhotoUpload).where(PendingPhotoUpload.admin_user_id == admin_user.id)
        )
    ).scalars().all()
    assert len(rows) == 1
    assert rows[0].owner_id == svc2.id


@pytest.mark.asyncio
async def test_delete_photo_admin_only(
    client, db_session, admin_user, client_user, settings
) -> None:
    p = Photo(
        owner_type=PhotoOwnerType.SERVICE, owner_id=1,
        telegram_file_id="fid", telegram_file_unique_id="uid",
        mime_type="image/jpeg", sort_order=0,
    )
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)

    res = await client.delete(
        f"/api/v1/admin/photos/{p.id}",
        headers=auth_headers(client_user, settings),
    )
    assert res.status_code == 403

    res = await client.delete(
        f"/api/v1/admin/photos/{p.id}",
        headers=auth_headers(admin_user, settings),
    )
    assert res.status_code == 204


@pytest.mark.asyncio
async def test_patch_photo_sort_updates(
    client, db_session, admin_user, settings
) -> None:
    p = Photo(
        owner_type=PhotoOwnerType.SERVICE, owner_id=1,
        telegram_file_id="fid", telegram_file_unique_id="uid",
        mime_type="image/jpeg", sort_order=0,
    )
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)

    res = await client.patch(
        f"/api/v1/admin/photos/{p.id}/sort",
        json={"sort_order": 5},
        headers=auth_headers(admin_user, settings),
    )
    assert res.status_code == 200, res.text
    await db_session.refresh(p)
    assert p.sort_order == 5


@pytest.mark.asyncio
async def test_proxy_unknown_photo_404(client) -> None:
    res = await client.get("/api/v1/photos/999999")
    assert res.status_code == 404
