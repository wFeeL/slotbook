from fastapi import APIRouter

from app.api.routes import admin, auth, bookings, branches, services, slots, staff

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(branches.router)
api_router.include_router(services.router)
api_router.include_router(staff.router)
api_router.include_router(slots.router)
api_router.include_router(bookings.router)
api_router.include_router(admin.router)
