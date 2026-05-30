"""Signal-layer model + migration tests (no live DB).

Imports the finance ORM, asserts the new tables are registered in the shared
metadata, and inspects the hand-written 0002 migration's identifiers and DDL
against the ORM — mirroring ``test_phase1_migration.py``.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest
from newskoo.models import Base, EntitySecurity, Security, Signal

# backend/tests/ -> backend/ -> backend/alembic/versions/0002_finance.py
_MIGRATION_PATH = (
    Path(__file__).resolve().parents[1] / "alembic" / "versions" / "0002_finance.py"
)

_FINANCE_TABLES = {"securities", "entity_securities", "signals"}


@pytest.fixture(scope="module")
def migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("finance_0002", _MIGRATION_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def source() -> str:
    return _MIGRATION_PATH.read_text(encoding="utf-8")


def test_models_importable() -> None:
    # The three models are importable from the package root (so Alembic metadata
    # and callers both see them).
    assert Security.__tablename__ == "securities"
    assert EntitySecurity.__tablename__ == "entity_securities"
    assert Signal.__tablename__ == "signals"


def test_metadata_includes_finance_tables() -> None:
    assert set(Base.metadata.tables) >= _FINANCE_TABLES


def test_migration_file_exists() -> None:
    assert _MIGRATION_PATH.is_file()


def test_revision_identifiers(migration: ModuleType) -> None:
    assert migration.revision == "0002"
    assert migration.down_revision == "0001"


def test_upgrade_downgrade_callable(migration: ModuleType) -> None:
    assert callable(migration.upgrade)
    assert callable(migration.downgrade)


def test_all_finance_tables_created(source: str) -> None:
    for table in _FINANCE_TABLES:
        assert f'create_table(\n        "{table}"' in source, f"missing create_table {table}"


def test_all_finance_tables_dropped(source: str) -> None:
    for table in _FINANCE_TABLES:
        assert f'drop_table("{table}")' in source, f"missing drop_table {table}"


def test_unique_symbol_index(source: str) -> None:
    assert '"ix_securities_symbol", "securities", ["symbol"], unique=True' in source


def test_name_index(source: str) -> None:
    assert '"ix_securities_name", "securities", ["name"]' in source


def test_signals_composite_index(source: str) -> None:
    assert '"ix_signals_security_as_of", "signals", ["security_id", "as_of"]' in source


def test_hnsw_embedding_index(source: str) -> None:
    assert "ix_securities_embedding" in source
    assert "USING hnsw" in source
    assert "vector_cosine_ops" in source
    assert "ivfflat" not in source


def test_entity_security_composite_pk(source: str) -> None:
    assert 'PrimaryKeyConstraint("entity_id", "security_id")' in source


def test_fk_cascade_rules(source: str) -> None:
    # entities + securities FKs cascade-delete (per the ORM).
    assert '["entities.id"], ondelete="CASCADE"' in source
    assert '["securities.id"], ondelete="CASCADE"' in source


def test_signals_columns_present(source: str) -> None:
    for col in (
        '"score"',
        '"direction"',
        '"magnitude"',
        '"confidence"',
        '"components"',
        '"supporting_article_ids"',
        '"supporting_event_ids"',
        '"horizon_hours"',
        '"as_of"',
    ):
        assert col in source, f"missing signals column {col}"


def test_security_model_columns() -> None:
    cols = set(Security.__table__.columns.keys())
    assert {
        "id",
        "symbol",
        "name",
        "exchange",
        "mic",
        "country",
        "asset_class",
        "aliases",
        "metadata",
        "embedding",
        "created_at",
        "updated_at",
    } <= cols


def test_signal_model_is_append_only() -> None:
    # Signals are point-in-time: created_at but no updated_at.
    cols = set(Signal.__table__.columns.keys())
    assert "created_at" in cols
    assert "updated_at" not in cols
