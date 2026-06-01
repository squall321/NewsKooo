"""Seed-catalog tests — validate breadth and integrity (no DB/network)."""

from __future__ import annotations

import pytest
from newskoo.sources.schemas import SourceCreate
from newskoo.sources.seeds import SEED_SOURCES

VALID_METHODS = {"rss", "api", "html"}


def test_catalog_size_meets_floor() -> None:
    assert len(SEED_SOURCES) >= 180, f"only {len(SEED_SOURCES)} seeds"


def test_every_entry_validates_as_source_create() -> None:
    for entry in SEED_SOURCES:
        model = SourceCreate.model_validate(entry)
        assert model.name
        assert model.homepage_url


def test_no_duplicate_feed_urls() -> None:
    feeds = [s["feed_url"] for s in SEED_SOURCES if s["feed_url"]]
    dupes = {f for f in feeds if feeds.count(f) > 1}
    assert not dupes, f"duplicate feed_urls: {dupes}"


def test_no_duplicate_upsert_identity() -> None:
    # upsert keys on feed_url else homepage_url; identities must be unique so
    # every seed persists as its own row.
    ids = [s["feed_url"] or s["homepage_url"] for s in SEED_SOURCES]
    dupes = {i for i in ids if ids.count(i) > 1}
    assert not dupes, f"colliding upsert identities: {dupes}"


def test_all_fetch_methods_valid() -> None:
    for s in SEED_SOURCES:
        assert s["fetch_method"] in VALID_METHODS, s["name"]


def test_rss_entries_have_feed_url() -> None:
    for s in SEED_SOURCES:
        if s["fetch_method"] == "rss":
            assert s["feed_url"], f"{s['name']} is rss but has no feed_url"


def test_bot_sensitivity_in_range() -> None:
    for s in SEED_SOURCES:
        assert 0 <= s["bot_sensitivity"] <= 3, s["name"]


def test_includes_science_category() -> None:
    cats = {c for s in SEED_SOURCES for c in s["categories"]}
    assert "science" in cats


def test_includes_non_english_languages() -> None:
    langs = {lang for s in SEED_SOURCES for lang in s["languages"]}
    # The platform must store original-language text — require key non-English ones.
    for required in ("ko", "ja", "ar"):
        assert required in langs, f"missing language {required}"


def test_region_breadth() -> None:
    regions = {s["region"] for s in SEED_SOURCES}
    assert len(regions) >= 8, f"only {len(regions)} distinct regions"


def test_category_breadth_covers_all_domains() -> None:
    cats = {c for s in SEED_SOURCES for c in s["categories"]}
    # boundary-less coverage: general + economy/finance + tech + science + niche.
    for required in ("general", "economy", "technology", "science", "niche", "finance"):
        assert required in cats, f"missing category {required}"


def test_has_arxiv_and_eurekalert_science_feeds() -> None:
    feeds = {s["feed_url"] for s in SEED_SOURCES if s["feed_url"]}
    names = {s["name"] for s in SEED_SOURCES}
    # arXiv migrated its feeds to rss.arxiv.org (2024); EurekAlert retired its
    # static RSS so it's crawled as html — but both remain in the catalog.
    assert any("rss.arxiv.org/rss" in f for f in feeds)
    assert any("EurekAlert" in n for n in names)


def test_includes_api_sources() -> None:
    api_kinds = {s["api_kind"] for s in SEED_SOURCES if s["api_kind"]}
    assert "gdelt" in api_kinds
    assert "newsapi" in api_kinds


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
