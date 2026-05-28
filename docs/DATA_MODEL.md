# NewsKoo — Data Model

PostgreSQL 16 + `pgvector` + full-text search. Designed so an LLM (or analyst) can retrieve **coherent context** quickly: source → article → entities/keywords → event → report. Text only (title + body); no image storage.

## Design principles
- **Original-language storage.** `articles.language` records the detected language; body/title kept verbatim. Analysis operates on the original; any translations live in `analysis` as derived data.
- **Idempotency.** Articles are upserted on `(canonical_url)` with a `content_hash` to detect revisions → `article_versions`.
- **Events over articles.** The same real-world story across many outlets/languages clusters into one `event`, the unit most useful for "what's happening" and issue detection.
- **Searchable two ways.** `tsvector` (lexical, per-language config) + `pgvector` embeddings (semantic, cross-language).
- **Scale.** `articles` and `crawl_log` are **range-partitioned by `published_at` / `fetched_at`** (monthly). Heavy time-series queries hit recent partitions.

## Core tables

### `sources`
Registry of where news comes from.
| column | type | notes |
|--------|------|-------|
| id | bigint PK | |
| name | text | display name |
| homepage_url | text | |
| feed_url | text null | RSS/Atom if any |
| api_kind | text null | `gdelt`/`newsapi`/`publisher`/null |
| fetch_method | text | `rss`/`api`/`html` |
| region | text | ISO country/region |
| languages | text[] | expected languages |
| categories | text[] | economy, science, tech, … |
| bot_sensitivity | smallint | 0–3 → politeness tier |
| politeness | jsonb | rate limits, delays, UA policy |
| robots_url | text null | |
| enabled | bool | |
| health | jsonb | last_ok, error_rate, latency |
| created_at / updated_at | timestamptz | |

### `articles` (partitioned by `published_at` monthly)
| column | type | notes |
|--------|------|-------|
| id | bigint | PK (id, published_at) |
| source_id | bigint FK | |
| canonical_url | text | unique within partition window; dedup key |
| url | text | fetched url |
| title | text | |
| body | text | clean article text |
| language | text | detected ISO code |
| authors | text[] | |
| published_at | timestamptz | partition key |
| fetched_at | timestamptz | |
| content_hash | bytea | for revision detection |
| simhash | bigint | near-dup detection (C++) |
| word_count | int | |
| tsv | tsvector | generated, language-aware FTS |
| embedding | vector(1024) | semantic search (nullable until analyzed) |
| event_id | bigint null FK | cluster membership |
| status | text | parsed/analyzed/error |

Indexes: `GIN(tsv)`, `ivfflat(embedding vector_cosine_ops)`, `btree(source_id, published_at)`, `btree(simhash)`, unique `(canonical_url, published_at)`.

### `article_versions`
Append-only history when a `canonical_url` re-fetches with a new `content_hash` (corrections, updates).

### `entities`
Canonical entity catalog (people, orgs, products, places, tickers).
| id | name | type | aliases text[] | metadata jsonb (e.g., ticker, wikidata_id) | embedding vector |

### `article_entities`
M:N article↔entity with `salience` (0–1), `count`, `sentiment`.

### `keywords` / `article_keywords`
Normalized keyword/phrase catalog + per-article weights (tf-idf / LLM-rated).

### `topics`
Hierarchical taxonomy (economy → markets → equities; science → physics → …). `article_topics` links with confidence.

### `events`
A clustered real-world story.
| id | title | summary | started_at | last_seen_at | article_count | source_count | language_count | centroid vector | score (issue strength) | metadata jsonb |

### `event_articles`
Membership with similarity score and `is_seed`.

### `analysis`
Derived LLM output per article or event (one row per (target, kind, provider)).
| id | target_type (article/event) | target_id | kind (summary/sentiment/translation/entities/…) | provider | model | result jsonb | tokens | cost | created_at |

### `reports`
Generated intelligence reports.
| id | query jsonb (keywords/sector/region/window) | title | body_md | citations jsonb (article/event ids) | provider/model | scheduled bool | version | created_at |

### `mention_timeseries`
Pre-aggregated counts for fast trend/issue detection.
| bucket (timestamptz, e.g. hourly) | target_type (entity/topic/keyword) | target_id | count | source_count | velocity | zscore |
PK `(target_type, target_id, bucket)`; powers the issue-detection engine and trend charts.

### `crawl_log` (partitioned by `fetched_at`)
Per-fetch outcome: source_id, url, http_status, bytes, latency_ms, method, ok, error, fetched_at. Feeds source health and politeness tuning.

## Relationships (text ERD)
```
sources 1───* articles *───1 events
articles *───* entities   (article_entities, salience/sentiment)
articles *───* keywords   (article_keywords, weight)
articles *───* topics     (article_topics, confidence)
articles/events 1───* analysis
entities/topics/keywords 1───* mention_timeseries
reports *··· cite ···* articles/events
```

## LLM-context query patterns
- **"What's the issue around X?"** → `mention_timeseries` (spike) → `events` (top by score) → `event_articles` → `articles` (multilingual bodies) → feed to LLM with citations.
- **Semantic recall** → `articles.embedding`/`events.centroid` cosine search, filtered by `published_at` window + `topics`.
- **Sector/product reports** → filter by `topics`/`entities` + window → cluster `events` → synthesize `reports` with `citations`.

Migrations live in `backend/alembic/`. The baseline migration creates extensions (`pgvector`, `pg_trgm`), partitioned parents, and indexes.
