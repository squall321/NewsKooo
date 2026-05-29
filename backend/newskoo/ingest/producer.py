"""Emit collected items onto Kafka ``raw.documents``.

Connectors yield loosely-typed item dicts (shaped like the non-frozen fields of
:class:`~newskoo.core.contracts.RawDocument`). :func:`emit_raw` stamps the
``source_id`` / ``fetched_at`` / ``fetch_method`` envelope, normalizes the
optional hint fields, and publishes via :func:`newskoo.core.kafka.publish`,
keyed on ``canonical_url`` (preferred) or ``url`` for idempotent partitioning.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Protocol

from newskoo.core.contracts import FetchMethod, RawDocument, Topic
from newskoo.core.kafka import publish
from newskoo.core.logging import get_logger

log = get_logger(__name__)


class _Producer(Protocol):
    """Minimal structural type for whatever publishes (real or fake).

    Matches :class:`aiokafka.AIOKafkaProducer` enough for
    :func:`newskoo.core.kafka.publish`, which calls ``send_and_wait(topic,
    payload, key=...)`` and lets the producer's value-serializer encode the
    Pydantic model. A test fake simply records the calls.
    """

    async def send_and_wait(
        self, topic: str, value: Any, *, key: bytes | None = ...
    ) -> Any: ...


def _coerce_dt(value: Any) -> datetime | None:
    """Best-effort coercion of a publish-date hint to an aware ``datetime``."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        try:
            from dateutil import parser as _dtp

            dt = _dtp.parse(value)
            return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
        except (ValueError, OverflowError, TypeError):
            return None
    return None


def build_raw_document(
    source_id: int, item: dict[str, Any], fetch_method: FetchMethod | str
) -> RawDocument:
    """Construct a :class:`RawDocument` from a connector item dict.

    Recognized item keys: ``url`` (required), ``canonical_url``, ``raw_html``,
    ``raw_text``, ``content`` / ``summary`` (mapped to ``raw_html`` if neither
    raw field set), ``title`` / ``title_hint``, ``published`` /
    ``published_at_hint``, ``http_status``, ``content_type``, ``headers``.
    """
    method = (
        fetch_method if isinstance(fetch_method, FetchMethod) else FetchMethod(fetch_method)
    )
    url = item.get("url")
    if not url:
        raise ValueError("item is missing required 'url'")

    raw_html = item.get("raw_html")
    raw_text = item.get("raw_text")
    if raw_html is None and raw_text is None:
        # RSS items often carry HTML in content/summary; treat as raw_html.
        raw_html = item.get("content") or item.get("summary")

    published = item.get("published_at_hint", item.get("published"))
    headers = item.get("headers") or {}

    return RawDocument(
        source_id=source_id,
        url=str(url),
        canonical_url=item.get("canonical_url"),
        fetch_method=method,
        http_status=item.get("http_status"),
        content_type=item.get("content_type"),
        raw_html=raw_html,
        raw_text=raw_text,
        title_hint=item.get("title_hint", item.get("title")),
        published_at_hint=_coerce_dt(published),
        fetched_at=datetime.now(UTC),
        headers={str(k): str(v) for k, v in dict(headers).items()},
    )


async def emit_raw(
    producer: _Producer,
    source_id: int,
    item: dict[str, Any],
    fetch_method: FetchMethod | str,
) -> RawDocument:
    """Build a ``RawDocument`` from ``item`` and publish it to ``raw.documents``.

    Returns the published document (handy for tests / metrics). The Kafka key is
    the canonical URL when present, else the fetched URL.
    """
    doc = build_raw_document(source_id, item, fetch_method)
    key = doc.canonical_url or doc.url
    await publish(producer, Topic.RAW_DOCUMENTS, doc, key=key)
    log.debug("ingest.emit_raw", source_id=source_id, url=doc.url, method=str(doc.fetch_method))
    return doc
