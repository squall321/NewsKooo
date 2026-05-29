"""Prometheus metrics: a small set of counters/gauges + an ASGI ``/metrics``.

The collectors here are intentionally lightweight — request counting/latency and
a couple of domain gauges the dashboard can scrape. They are registered against
the default global registry so any ``prometheus_client`` collector elsewhere in
the process is exported too.

``mount_metrics(app)`` wires:
- an HTTP middleware that records request count + latency by method/path/status;
- a ``GET /metrics`` route serving the Prometheus text exposition format.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# ── Collectors ───────────────────────────────────────────────────────────────
HTTP_REQUESTS = Counter(
    "newskoo_http_requests_total",
    "Total HTTP requests handled by the API.",
    labelnames=("method", "path", "status"),
)
HTTP_LATENCY = Histogram(
    "newskoo_http_request_duration_seconds",
    "HTTP request latency in seconds.",
    labelnames=("method", "path"),
)
SEARCH_QUERIES = Counter(
    "newskoo_search_queries_total",
    "Search queries executed, by mode.",
    labelnames=("mode",),
)
ISSUE_STREAM_CLIENTS = Gauge(
    "newskoo_issue_stream_clients",
    "Currently connected issue SSE clients.",
)
WS_STATS_CLIENTS = Gauge(
    "newskoo_ws_stats_clients",
    "Currently connected stats WebSocket clients.",
)


def _route_template(request: Request) -> str:
    """Use the matched route's path template (low cardinality) when available.

    Falls back to the raw path. Using the template (``/api/sources/{source_id}``)
    instead of the concrete path keeps label cardinality bounded.
    """
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    return path or request.url.path


async def _metrics_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    start = time.perf_counter()
    response: Response | None = None
    try:
        response = await call_next(request)
        return response
    finally:
        path = _route_template(request)
        # Don't account the /metrics scrape itself.
        if path != "/metrics":
            status = response.status_code if response is not None else 500
            HTTP_LATENCY.labels(request.method, path).observe(
                time.perf_counter() - start
            )
            HTTP_REQUESTS.labels(request.method, path, str(status)).inc()


async def _metrics_endpoint(_request: Request) -> Response:
    # Starlette route endpoints receive the request; we don't need it here.
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def mount_metrics(app: FastAPI) -> None:
    """Attach the metrics middleware and the ``/metrics`` route to ``app``."""
    app.middleware("http")(_metrics_middleware)
    app.add_route("/metrics", _metrics_endpoint, methods=["GET"], include_in_schema=False)
