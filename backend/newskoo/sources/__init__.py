"""Source registry & discovery (Phase 2): catalog CRUD, RSS autodiscovery,
sitemap/OPML import, the connector seam to ingestion, and the seeded worldwide
source list.

Public API is re-exported here so callers can ``from newskoo.sources import ...``.
"""

from __future__ import annotations

from newskoo.sources.connectors import (
    CONNECTOR_REGISTRY,
    SourceConnector,
    connector_name_for,
    register_connector,
)
from newskoo.sources.discovery import (
    discover_feeds,
    extract_feed_links,
    import_opml,
    parse_sitemap,
    parse_sitemap_xml,
)
from newskoo.sources.registry import (
    create_source,
    get_by_feed_or_home,
    get_source,
    list_sources,
    record_health,
    set_enabled,
    update_source,
    upsert_source,
)
from newskoo.sources.schemas import (
    FetchMethod,
    PolitenessPolicy,
    SourceCreate,
    SourceOut,
    SourceUpdate,
    politeness_for,
)
from newskoo.sources.seeds import SEED_SOURCES, seed_sources

__all__ = [
    "CONNECTOR_REGISTRY",
    # seeds
    "SEED_SOURCES",
    "FetchMethod",
    # schemas
    "PolitenessPolicy",
    # connectors
    "SourceConnector",
    "SourceCreate",
    "SourceOut",
    "SourceUpdate",
    "connector_name_for",
    # registry CRUD
    "create_source",
    # discovery
    "discover_feeds",
    "extract_feed_links",
    "get_by_feed_or_home",
    "get_source",
    "import_opml",
    "list_sources",
    "parse_sitemap",
    "parse_sitemap_xml",
    "politeness_for",
    "record_health",
    "register_connector",
    "seed_sources",
    "set_enabled",
    "update_source",
    "upsert_source",
]
