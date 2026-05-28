"""FastAPI application entrypoint.

Routers for sources/articles/events/search/trends/issues/reports are added in
Phase 7 under ``newskoo/api/routers/``. This module wires the app, CORS,
lifespan, health, and metrics.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from newskoo.core.config import get_settings
from newskoo.core.db import dispose_engine
from newskoo.core.logging import configure_logging, get_logger

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    log.info("api.startup", env=get_settings().environment)
    yield
    await dispose_engine()
    log.info("api.shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="NewsKoo API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["meta"])
    async def health() -> dict:
        return {"status": "ok", "service": "newskoo-api", "version": "0.1.0"}

    # Phase 7 routers are registered here:
    #   from newskoo.api.routers import sources, articles, events, search, ...
    #   app.include_router(sources.router, prefix="/api")
    return app


app = create_app()
