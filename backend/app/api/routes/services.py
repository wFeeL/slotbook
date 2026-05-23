from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.db.repositories.businesses import BusinessesRepo
from app.db.repositories.services import ServicesRepo
from app.schemas.services import ServiceRead

router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=list[ServiceRead])
async def list_services(
    _user: CurrentUser, session: SessionDep, branch_id: int | None = None
) -> list[ServiceRead]:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None, "Business must be bootstrapped at startup"
    services = await ServicesRepo(session).list_active(business.id, branch_id=branch_id)
    return [ServiceRead.model_validate(s) for s in services]
