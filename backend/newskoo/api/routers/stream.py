"""Live streaming endpoints.

- ``GET /stream/issues`` — Server-Sent Events of :class:`IssueAlert`s consumed
  from Kafka ``issues.alerts`` in real time. Each connection gets its own
  consumer group (so every client sees every alert) reading from the *latest*
  offset (only new alerts, not history). If Kafka is unavailable the stream
  degrades to periodic heartbeat comments so the HTTP connection stays healthy
  and the client can keep retrying.

- ``WS /ws/stats`` — a WebSocket that pushes live ingestion/DB stats (article /
  event / source counts) on an interval; the client may also send text frames
  and receives a ``pong`` reply.

Both are defensive: a single client connecting must never crash the app, and a
down Kafka/DB must not wedge the event loop.
"""

from __future__ import annotations

import asyncio
import contextlib
import uuid
from collections.abc import AsyncIterator
from typing import Any

import orjson
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from newskoo.api.deps import SessionDep
from newskoo.api.metrics import ISSUE_STREAM_CLIENTS, WS_STATS_CLIENTS
from newskoo.core.config import get_settings
from newskoo.core.contracts import IssueAlert, Topic
from newskoo.core.logging import get_logger
from newskoo.models.article import Article
from newskoo.models.event import Event
from newskoo.models.source import Source

router = APIRouter(tags=["stream"])
log = get_logger(__name__)

# Heartbeat cadence (seconds) when idle / Kafka unavailable.
_HEARTBEAT_S = 15.0
# Stats push cadence (seconds) for the WebSocket.
_STATS_INTERVAL_S = 5.0


async def _make_issue_consumer() -> Any | None:
    """Create a per-connection Kafka consumer on ``issues.alerts`` (latest offset).

    Returns ``None`` (and logs) if the broker is unreachable, so the SSE handler
    can fall back to heartbeats instead of failing the request.
    """
    settings = get_settings()
    try:
        from aiokafka import AIOKafkaConsumer

        consumer = AIOKafkaConsumer(
            str(Topic.ISSUES_ALERTS),
            bootstrap_servers=settings.kafka_bootstrap_servers,
            client_id=settings.kafka_client_id,
            # Unique group per connection ⇒ fan-out (every client gets every msg).
            group_id=f"{settings.kafka_consumer_group_prefix}.api.issues.{uuid.uuid4().hex}",
            value_deserializer=orjson.loads,
            enable_auto_commit=False,
            auto_offset_reset="latest",
        )
        await consumer.start()
        return consumer
    except Exception as exc:  # broker down / misconfigured
        log.warning(
            "stream.kafka_unavailable", error=str(exc), error_type=type(exc).__name__
        )
        return None


async def _issue_event_generator(request: Request) -> AsyncIterator[dict]:
    """Yield SSE events: ``issue`` events from Kafka, ``heartbeat`` when idle."""
    consumer = await _make_issue_consumer()
    ISSUE_STREAM_CLIENTS.inc()
    try:
        if consumer is None:
            # Degraded mode: keepalives only until the client gives up / Kafka returns.
            while not await request.is_disconnected():
                yield {"event": "heartbeat", "data": "{}"}
                await asyncio.sleep(_HEARTBEAT_S)
            return

        while not await request.is_disconnected():
            # Wait for messages but wake periodically to send heartbeats and
            # re-check client disconnection.
            batch = await consumer.getmany(
                timeout_ms=int(_HEARTBEAT_S * 1000), max_records=50
            )
            if not batch:
                yield {"event": "heartbeat", "data": "{}"}
                continue

            for _tp, messages in batch.items():
                for msg in messages:
                    try:
                        alert = IssueAlert.model_validate(msg.value)
                    except Exception as exc:  # malformed payload — skip, don't die
                        log.warning("stream.bad_alert", error=str(exc))
                        continue
                    yield {
                        "event": "issue",
                        "id": f"{alert.target_type}:{alert.target_id}",
                        "data": alert.model_dump_json(),
                    }
    except asyncio.CancelledError:  # pragma: no cover - client disconnect path
        raise
    finally:
        ISSUE_STREAM_CLIENTS.dec()
        if consumer is not None:
            with contextlib.suppress(Exception):
                await consumer.stop()


@router.get("/stream/issues")
async def stream_issues(request: Request) -> EventSourceResponse:
    """SSE stream of live issue alerts (Kafka ``issues.alerts``)."""
    return EventSourceResponse(_issue_event_generator(request))


async def _collect_stats(session: AsyncSession) -> dict:
    """Snapshot of headline counts for the dashboard."""
    articles = int(await session.scalar(select(func.count()).select_from(Article)) or 0)
    events = int(await session.scalar(select(func.count()).select_from(Event)) or 0)
    sources = int(await session.scalar(select(func.count()).select_from(Source)) or 0)
    enabled_sources = int(
        await session.scalar(
            select(func.count()).select_from(Source).where(Source.enabled.is_(True))
        )
        or 0
    )
    return {
        "articles": articles,
        "events": events,
        "sources": sources,
        "enabled_sources": enabled_sources,
    }


@router.websocket("/ws/stats")
async def ws_stats(websocket: WebSocket, session: AsyncSession = SessionDep) -> None:
    """Push live ingestion/DB stats every few seconds over a WebSocket."""
    await websocket.accept()
    WS_STATS_CLIENTS.inc()
    log.info("stream.ws_stats_connected")

    async def _receiver() -> None:
        """Drain inbound frames; reply pong to anything, exit on disconnect."""
        try:
            while True:
                await websocket.receive_text()
                with contextlib.suppress(Exception):
                    await websocket.send_text('{"type":"pong"}')
        except WebSocketDisconnect:
            return

    receiver = asyncio.create_task(_receiver())
    try:
        while not receiver.done():
            try:
                stats = await _collect_stats(session)
                await websocket.send_text(
                    orjson.dumps({"type": "stats", **stats}).decode()
                )
            except Exception as exc:  # DB hiccup shouldn't drop the socket
                log.warning("stream.stats_failed", error=str(exc))
            await asyncio.sleep(_STATS_INTERVAL_S)
    except WebSocketDisconnect:  # pragma: no cover - disconnect path
        pass
    finally:
        receiver.cancel()
        with contextlib.suppress(Exception, asyncio.CancelledError):
            await receiver
        WS_STATS_CLIENTS.dec()
        log.info("stream.ws_stats_disconnected")
