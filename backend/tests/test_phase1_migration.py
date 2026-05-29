"""Phase-1 tests: the hand-written baseline migration.

No live database is required — we load the migration module from its file path
and inspect its identifiers, callables, and SQL/op references against the ORM.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest
from newskoo.models import Base

# backend/tests/ -> backend/ -> backend/alembic/versions/0001_baseline.py
_MIGRATION_PATH = (
    Path(__file__).resolve().parents[1] / "alembic" / "versions" / "0001_baseline.py"
)

# Every table the ORM declares; the migration must create all of them.
_EXPECTED_TABLES = {
    "sources",
    "articles",
    "article_versions",
    "entities",
    "article_entities",
    "keywords",
    "article_keywords",
    "topics",
    "article_topics",
    "events",
    "event_articles",
    "analysis",
    "reports",
    "mention_timeseries",
    "crawl_log",
}


@pytest.fixture(scope="module")
def migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("phase1_baseline", _MIGRATION_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def source() -> str:
    return _MIGRATION_PATH.read_text(encoding="utf-8")


def test_migration_file_exists() -> None:
    assert _MIGRATION_PATH.is_file()


def test_revision_identifiers(migration: ModuleType) -> None:
    assert migration.revision == "0001"
    assert migration.down_revision is None


def test_upgrade_downgrade_callable(migration: ModuleType) -> None:
    assert callable(migration.upgrade)
    assert callable(migration.downgrade)


def test_orm_table_set_matches_expectation() -> None:
    # Guard: the expected set tracks exactly the ORM metadata tables.
    assert set(Base.metadata.tables) == _EXPECTED_TABLES


def test_all_tables_created(source: str) -> None:
    for table in _EXPECTED_TABLES:
        assert f'create_table(\n        "{table}"' in source, f"missing create_table for {table}"


def test_all_tables_dropped(source: str) -> None:
    for table in _EXPECTED_TABLES:
        assert f'drop_table("{table}")' in source, f"missing drop_table for {table}"


def test_extensions_seeded(source: str) -> None:
    assert "CREATE EXTENSION IF NOT EXISTS vector" in source
    assert "CREATE EXTENSION IF NOT EXISTS pg_trgm" in source


def test_hnsw_vector_indexes(source: str) -> None:
    # HNSW (not ivfflat) for all three embedding columns.
    assert "USING hnsw" in source
    assert "ivfflat" not in source
    assert "ix_articles_embedding" in source
    assert "ix_entities_embedding" in source
    assert "ix_events_centroid" in source
    assert "vector_cosine_ops" in source


def test_generated_tsv_column(source: str) -> None:
    assert "to_tsvector('simple'" in source
    assert "persisted=True" in source


def test_declared_indexes_present(source: str) -> None:
    for index in (
        "ix_articles_canonical_url",
        "ix_articles_source_published",
        "ix_articles_simhash",
        "ix_articles_tsv",
        "ix_article_entities_entity",
        "ix_article_keywords_keyword",
        "ix_article_topics_topic",
        "ix_analysis_target",
        "ix_crawl_log_source_time",
    ):
        assert index in source, f"missing index {index}"


def test_composite_pk_association_tables(source: str) -> None:
    assert 'PrimaryKeyConstraint("article_id", "entity_id")' in source
    assert 'PrimaryKeyConstraint("article_id", "keyword_id")' in source
    assert 'PrimaryKeyConstraint("article_id", "topic_id")' in source
    assert 'PrimaryKeyConstraint("event_id", "article_id")' in source
    assert 'PrimaryKeyConstraint("target_type", "target_id", "bucket")' in source


def test_fk_ondelete_rules(source: str) -> None:
    # A representative sample of the ON DELETE behaviours from the ORM.
    assert 'ondelete="CASCADE"' in source
    assert 'ondelete="SET NULL"' in source


def test_canonical_url_unique_index(source: str) -> None:
    assert '"ix_articles_canonical_url", "articles", ["canonical_url"], unique=True' in source
