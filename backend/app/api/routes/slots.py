from datetime import date

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, SessionDep
from app.db.repositories.businesses import BusinessesRepo
from app.schemas.slots import SlotsResponse
from app.services.slot_service import SlotService

router = APIRouter(prefix="/slots", tags=["slots"])


@router.get("", response_model=SlotsResponse)
async def list_slots(
    _user: CurrentUser,
    session: SessionDep,
    service_id: int = Query(..., gt=0),
    staff_id: int = Query(..., gt=0),
    date: date = Query(..., alias="date"),
) -> SlotsResponse:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    slots = await SlotService(session).list_available_slots(business, service_id, staff_id, date)
    return SlotsResponse(date=date.isoformat(), timezone=business.timezone, slots=slots)  # type: ignore[arg-type]
