from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import (
    Forbidden,
    NotFound,
    SlotAlreadyTaken,
    install_exception_handlers,
)


def _make_app() -> FastAPI:
    app = FastAPI()
    install_exception_handlers(app)

    @app.get("/raises-not-found")
    async def _nf() -> None:
        raise NotFound("Entity X not found")

    @app.get("/raises-slot-taken")
    async def _st() -> None:
        raise SlotAlreadyTaken(extra={"staff_id": 7})

    @app.get("/raises-forbidden")
    async def _fb() -> None:
        raise Forbidden()

    return app


def test_not_found_maps_to_404() -> None:
    client = TestClient(_make_app())
    response = client.get("/raises-not-found")
    assert response.status_code == 404
    assert response.json() == {"detail": {"code": "not_found", "message": "Entity X not found"}}


def test_slot_already_taken_maps_to_409_with_extra() -> None:
    client = TestClient(_make_app())
    response = client.get("/raises-slot-taken")
    assert response.status_code == 409
    body = response.json()
    assert body["detail"]["code"] == "slot_already_taken"
    assert body["detail"]["extra"] == {"staff_id": 7}


def test_forbidden_uses_default_message() -> None:
    client = TestClient(_make_app())
    response = client.get("/raises-forbidden")
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "forbidden"
