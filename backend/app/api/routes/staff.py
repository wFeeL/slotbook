from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, SessionDep
from app.db.repositories.businesses import BusinessesRepo
from app.db.repositories.staff import StaffRepo
from app.schemas.staff import StaffRead

router = APIRouter(prefix="/staff", tags=["staff"])


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
    return [StaffRead.model_validate(s) for s in staff]
