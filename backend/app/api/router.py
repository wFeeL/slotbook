from fastapi import APIRouter

from app.api.routes import (
    admin,
    auth,
    bookings,
    branches,
    photos,
    services,
    slots,
    staff,
    staff_me,
    users,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(branches.router)
api_router.include_router(photos.router)
api_router.include_router(services.router)
api_router.include_router(staff.router)
api_router.include_router(staff_me.router)
api_router.include_router(slots.router)
api_router.include_router(bookings.router)
api_router.include_router(admin.router)
