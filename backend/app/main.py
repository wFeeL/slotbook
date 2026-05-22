from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import health
from app.core.config import get_settings
from app.core.errors import install_exception_handlers
from app.core.logging import configure_logging
from app.db.repositories.businesses import BusinessesRepo
from app.db.session import get_sessionmaker


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        await BusinessesRepo(session).ensure_from_settings(
            name=settings.BUSINESS_NAME,
            timezone=settings.BUSINESS_TIMEZONE,
            booking_buffer_minutes=settings.BUSINESS_BOOKING_BUFFER_MINUTES,
            min_cancellation_hours=settings.BUSINESS_MIN_CANCELLATION_HOURS,
            slot_step_minutes=settings.BUSINESS_SLOT_STEP_MINUTES,
        )
        await session.commit()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)

    app = FastAPI(
        title="SlotBook API", version="0.1.0", debug=settings.APP_DEBUG, lifespan=lifespan
    )
    install_exception_handlers(app)
    app.include_router(health.router, tags=["health"])
    return app


app = create_app()
