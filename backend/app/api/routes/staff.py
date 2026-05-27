from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, SessionDep
from app.core.errors import NotFound
from app.db.enums import PhotoOwnerType
from app.db.repositories.businesses import BusinessesRepo
from app.db.repositories.photos import PhotosRepo
from app.db.repositories.staff import StaffRepo
from app.schemas.photos import to_photo_read
from app.schemas.staff import StaffRead

router = APIRouter(prefix="/staff", tags=["staff"])


def _enrich(stf, photos) -> StaffRead:
    data = StaffRead.model_validate(stf).model_dump()
    data["photos"] = [to_photo_read(p).model_dump() for p in photos]
    data["avg_rating"] = float(stf.avg_rating) if stf.avg_rating is not None else None
    data["review_count"] = stf.review_count
    return StaffRead(**data)


@router.get("", response_model=list[StaffRead])
async def list_staff(
    _user: CurrentUser,
    session: SessionDep,
    service_id: int = Query(..., gt=0),
    branch_id: int | None = None,
) -> list[StaffRead]:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    staff = await StaffRepo(session).list_for_service(
        business.id, service_id, branch_id=branch_id
    )
    if not staff:
        return []
    photos_by_owner = await PhotosRepo(session).list_for_owners(
        PhotoOwnerType.STAFF, [s.id for s in staff]
    )
    return [_enrich(s, photos_by_owner.get(s.id, [])) for s in staff]


@router.get("/{staff_id}", response_model=StaffRead)
async def get_staff(
    staff_id: int, _user: CurrentUser, session: SessionDep
) -> StaffRead:
    stf = await StaffRepo(session).get(staff_id)
    if stf is None or not stf.is_active:
        raise NotFound("Staff member not found")
    photos = await PhotosRepo(session).list_for_owner(PhotoOwnerType.STAFF, stf.id)
    return _enrich(stf, photos)
