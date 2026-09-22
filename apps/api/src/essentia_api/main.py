from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from essentia_api.api.router import api_router
from essentia_api.api.routes.health import router as health_router
from essentia_api.core.config import (
    Settings,
    load_settings,
)
from essentia_api.db.pool import create_connection_pool


def create_app(
    settings: Settings | None = None,
) -> FastAPI:
    """
    Create an isolated FastAPI application instance.

    When no Settings object is supplied, configuration is loaded from the
    current process environment. Tests inject their own Settings instance,
    so they never depend on cached or import-time production configuration.
    """
    app_settings = settings or load_settings()

    @asynccontextmanager
    async def lifespan(
        app: FastAPI,
    ) -> AsyncIterator[None]:
        pool = create_connection_pool(
            app_settings,
        )

        app.state.db_pool = pool

        try:
            pool.open(
                wait=True,
            )
            yield
        finally:
            pool.close()

    app = FastAPI(
        title="Essentia AI Medical Scheduling Assistant API",
        description=(
            "REST API for medical scheduling and "
            "administrative workflows."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    app.state.settings = app_settings

    app.include_router(health_router)
    app.include_router(api_router)

    return app
