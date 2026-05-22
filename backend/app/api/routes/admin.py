from fastapi import APIRouter, status

from app.api.deps import AdminUser, SessionDep
from app.core.errors import NotFound
from app.db.models.schedule import ScheduleException, WorkingHours
from app.db.models.service import Service
from app.db.models.staff import StaffMember
from app.db.repositories.businesses import BusinessesRepo
from app.db.repositories.schedules import ScheduleExceptionsRepo, WorkingHoursRepo
from app.db.repositories.services import ServicesRepo
from app.db.repositories.staff import StaffRepo
from app.schemas.schedules import (
    ScheduleExceptionCreate,
    ScheduleExceptionRead,
    WorkingHoursEntry,
    WorkingHoursReplace,
)
from app.schemas.services import ServiceCreate, ServiceRead, ServiceUpdate
from app.schemas.staff import StaffCreate, StaffRead, StaffServicesUpdate, StaffUpdate

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


@router.post("/staff", response_model=StaffRead, status_code=status.HTTP_201_CREATED)
async def create_staff(body: StaffCreate, _admin: AdminUser, session: SessionDep) -> StaffRead:
    business = await BusinessesRepo(session).get_singleton()
    assert business is not None
    staff = StaffMember(business_id=business.id, name=body.name, description=body.description)
    StaffRepo(session).add(staff)
    await session.commit()
    await session.refresh(staff)
    return StaffRead.model_validate(staff)


@router.patch("/staff/{staff_id}", response_model=StaffRead)
async def update_staff(
    staff_id: int, body: StaffUpdate, _admin: AdminUser, session: SessionDep
) -> StaffRead:
    repo = StaffRepo(session)
    staff = await repo.get(staff_id)
    if staff is None:
        raise NotFound("Staff member not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(staff, field, value)
    await session.commit()
    await session.refresh(staff)
    return StaffRead.model_validate(staff)


@router.delete("/staff/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_staff(staff_id: int, _admin: AdminUser, session: SessionDep) -> None:
    repo = StaffRepo(session)
    staff = await repo.get(staff_id)
    if staff is None:
        raise NotFound("Staff member not found")
    staff.is_active = False
    await session.commit()


@router.put("/staff/{staff_id}/services", status_code=status.HTTP_204_NO_CONTENT)
async def replace_staff_services(
    staff_id: int, body: StaffServicesUpdate, _admin: AdminUser, session: SessionDep
) -> None:
    repo = StaffRepo(session)
    staff = await repo.get(staff_id)
    if staff is None:
        raise NotFound("Staff member not found")
    await repo.replace_services(staff_id, body.service_ids)
    await session.commit()


@router.get("/staff/{staff_id}/working-hours", response_model=list[WorkingHoursEntry])
async def get_working_hours(
    staff_id: int, _admin: AdminUser, session: SessionDep
) -> list[WorkingHoursEntry]:
    if (await StaffRepo(session).get(staff_id)) is None:
        raise NotFound("Staff member not found")
    rows = await WorkingHoursRepo(session).list_for_staff(staff_id)
    return [WorkingHoursEntry.model_validate(r) for r in rows]


@router.put("/staff/{staff_id}/working-hours", status_code=status.HTTP_204_NO_CONTENT)
async def put_working_hours(
    staff_id: int, body: WorkingHoursReplace, _admin: AdminUser, session: SessionDep
) -> None:
    if (await StaffRepo(session).get(staff_id)) is None:
        raise NotFound("Staff member not found")
    entries = [
        WorkingHours(
            staff_id=staff_id,
            weekday=e.weekday,
            start_time=e.start_time,
            end_time=e.end_time,
            is_active=e.is_active,
        )
        for e in body.entries
    ]
    await WorkingHoursRepo(session).replace_for_staff(staff_id, entries)
    await session.commit()


@router.post(
    "/staff/{staff_id}/exceptions",
    response_model=ScheduleExceptionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_exception(
    staff_id: int, body: ScheduleExceptionCreate, _admin: AdminUser, session: SessionDep
) -> ScheduleExceptionRead:
    if (await StaffRepo(session).get(staff_id)) is None:
        raise NotFound("Staff member not found")
    exception = ScheduleException(
        staff_id=staff_id,
        date=body.date,
        type=body.type,
        start_time=body.start_time,
        end_time=body.end_time,
        reason=body.reason,
    )
    ScheduleExceptionsRepo(session).add(exception)
    await session.commit()
    await session.refresh(exception)
    return ScheduleExceptionRead.model_validate(exception)


@router.delete(
    "/staff/{staff_id}/exceptions/{exception_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_exception(
    staff_id: int, exception_id: int, _admin: AdminUser, session: SessionDep
) -> None:
    if (await StaffRepo(session).get(staff_id)) is None:
        raise NotFound("Staff member not found")
    deleted = await ScheduleExceptionsRepo(session).delete(exception_id)
    if not deleted:
        raise NotFound("Exception not found")
    await session.commit()
