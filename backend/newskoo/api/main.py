"""FastAPI application entrypoint.

Wires the app, CORS, lifespan, health, Prometheus ``/metrics``, and the Phase-7
routers (sources / articles / events / search / trends / issues / reports /
stream) under the ``/api`` prefix.

Read endpoints are open; mutations require the API key when ``settings.api_key``
is configured (enforced per-route via :data:`newskoo.api.deps.AuthDep`).
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from newskoo.api.metrics import mount_metrics
from newskoo.api.routers import (
    articles,
    events,
    issues,
    reports,
    search,
    sources,
    stream,
    trends,
)
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

    # REST + streaming routers under /api.
    for module in (sources, articles, events, search, trends, issues, reports, stream):
        app.include_router(module.router, prefix="/api")

    # Prometheus /metrics + request middleware.
    mount_metrics(app)
    return app


app = create_app()
