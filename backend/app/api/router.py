from fastapi import APIRouter

from app.api.routes import admin, auth, services

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(services.router)
api_router.include_router(admin.router)
