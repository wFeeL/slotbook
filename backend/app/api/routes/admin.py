from fastapi import APIRouter, status

from app.api.deps import AdminUser, SessionDep
from app.core.errors import NotFound
from app.db.models.service import Service
from app.db.repositories.businesses import BusinessesRepo
from app.db.repositories.services import ServicesRepo
from app.schemas.services import ServiceCreate, ServiceRead, ServiceUpdate

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/services", response_model=ServiceRead, status_code=status.HTTP_201_CREATED)
async def create_service(
    body: ServiceCreate, _admin: AdminUser, session: SessionDep
) -> ServiceRead:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    service = Service(
        business_id=business.id,
        title=body.title,
        description=body.description,
        duration_minutes=body.duration_minutes,
        price=body.price,
        sort_order=body.sort_order,
    )
    ServicesRepo(session).add(service)
    await session.commit()
    await session.refresh(service)
    return ServiceRead.model_validate(service)


@router.patch("/services/{service_id}", response_model=ServiceRead)
async def update_service(
    service_id: int, body: ServiceUpdate, _admin: AdminUser, session: SessionDep
) -> ServiceRead:
    repo = ServicesRepo(session)
    service = await repo.get(service_id)
    if service is None:
        raise NotFound("Service not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(service, field, value)
    await session.commit()
    await session.refresh(service)
    return ServiceRead.model_validate(service)


@router.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(service_id: int, _admin: AdminUser, session: SessionDep) -> None:
    repo = ServicesRepo(session)
    service = await repo.get(service_id)
    if service is None:
        raise NotFound("Service not found")
    await repo.soft_delete(service)
    await session.commit()
