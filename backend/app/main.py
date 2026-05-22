from fastapi import FastAPI

from app.api.routes import health
from app.core.config import get_settings
from app.core.errors import install_exception_handlers
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)

    app = FastAPI(title="SlotBook API", version="0.1.0", debug=settings.APP_DEBUG)
    install_exception_handlers(app)
    app.include_router(health.router, tags=["health"])
    return app


app = create_app()
