from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.db.repositories.branches import BranchesRepo
from app.db.repositories.businesses import BusinessesRepo
from app.schemas.branches import BranchRead

router = APIRouter(prefix="/branches", tags=["branches"])


@router.get("", response_model=list[BranchRead])
async def list_branches(_user: CurrentUser, session: SessionDep) -> list[BranchRead]:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    branches = await BranchesRepo(session).list_for_business(business.id, include_archived=False)
    return [BranchRead.model_validate(b) for b in branches]
