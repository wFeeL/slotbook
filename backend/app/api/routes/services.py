from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.core.errors import NotFound
from app.db.enums import PhotoOwnerType
from app.db.repositories.businesses import BusinessesRepo
from app.db.repositories.photos import PhotosRepo
from app.db.repositories.services import ServicesRepo
from app.schemas.photos import to_photo_read
from app.schemas.services import ServiceRead

router = APIRouter(prefix="/services", tags=["services"])


def _enrich(svc, photos) -> ServiceRead:
    data = ServiceRead.model_validate(svc).model_dump()
    data["photos"] = [to_photo_read(p).model_dump() for p in photos]
    data["avg_rating"] = float(svc.avg_rating) if svc.avg_rating is not None else None
    data["review_count"] = svc.review_count
    return ServiceRead(**data)


@router.get("", response_model=list[ServiceRead])
async def list_services(
    _user: CurrentUser, session: SessionDep, branch_id: int | None = None
) -> list[ServiceRead]:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None, "Business must be bootstrapped at startup"
    services = await ServicesRepo(session).list_active(business.id, branch_id=branch_id)
    if not services:
        return []
    photos_by_owner = await PhotosRepo(session).list_for_owners(
        PhotoOwnerType.SERVICE, [s.id for s in services]
    )
    return [_enrich(s, photos_by_owner.get(s.id, [])) for s in services]


@router.get("/{service_id}", response_model=ServiceRead)
async def get_service(
    service_id: int, _user: CurrentUser, session: SessionDep
) -> ServiceRead:
    svc = await ServicesRepo(session).get(service_id)
    if svc is None:
        raise NotFound("Service not found")
    photos = await PhotosRepo(session).list_for_owner(PhotoOwnerType.SERVICE, svc.id)
    return _enrich(svc, photos)
