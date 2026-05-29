"""Connector contract: the seam between the source registry and Phase-3 ingestion.

This module is **interface-only**. It declares the :class:`SourceConnector`
protocol that ingestion collectors implement, plus a small registry mapping a
source's ``fetch_method`` to the (string) name of the concrete connector class
that Phase-3 will provide. Keeping the mapping to *strings* avoids importing the
not-yet-written ingestion code from the registry layer.

A connector turns a :class:`~newskoo.models.source.Source` into an async stream
of raw document dicts that the ingestion layer wraps into
:class:`newskoo.core.contracts.RawDocument` messages on ``raw.documents``.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from newskoo.models.source import Source


@runtime_checkable
class SourceConnector(Protocol):
    """Contract every ingestion collector implements.

    Implementations live in ``newskoo.ingest`` (Phase 3). They must be safe for
    concurrent use and must honor the source's politeness policy. ``fetch``
    yields loosely-typed dicts shaped like the non-frozen fields of
    :class:`newskoo.core.contracts.RawDocument` (``url``, ``raw_html`` /
    ``raw_text``, ``title_hint``, ``published_at_hint``, ``headers`` …); the
    ingestion layer stamps ``source_id`` / ``fetched_at`` and publishes.
    """

    #: ``fetch_method`` value this connector handles ("rss" | "api" | "html").
    fetch_method: str

    @abstractmethod
    def fetch(self, source: Source) -> AsyncIterator[dict]:
        """Yield raw document dicts discovered for ``source``.

        Note: declared without ``async`` in the Protocol so structural typing
        matches an ``async def`` returning an ``AsyncIterator`` in implementers.
        """
        ...


# fetch_method → fully-qualified connector class name (resolved lazily by Phase 3).
# Strings, not classes, so the registry never imports ingestion code.
CONNECTOR_REGISTRY: dict[str, str] = {
    "rss": "newskoo.ingest.rss.RssConnector",
    "api": "newskoo.ingest.api.ApiConnector",
    "html": "newskoo.ingest.html.HtmlConnector",
}


def connector_name_for(fetch_method: str) -> str:
    """Return the registered connector class path for a ``fetch_method``.

    Raises ``KeyError`` for an unknown method so misconfiguration fails loudly.
    """
    try:
        return CONNECTOR_REGISTRY[fetch_method]
    except KeyError as exc:  # pragma: no cover - defensive
        raise KeyError(
            f"No connector registered for fetch_method={fetch_method!r}. "
            f"Known: {sorted(CONNECTOR_REGISTRY)}"
        ) from exc


def register_connector(fetch_method: str, dotted_path: str) -> None:
    """Register/override the connector class path for a ``fetch_method``."""
    CONNECTOR_REGISTRY[fetch_method] = dotted_path
