/**
 * Wire types mirroring the NewsKoo FastAPI schemas (backend `api/schemas.py`).
 * These are the exact shapes returned by `/api/*` and consumed by the SSE/WS
 * streams. Keep in sync with the backend Pydantic models.
 */

// ── Generic pagination envelope ──────────────────────────────────────────────
export interface Paginated<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

// ── Sources ──────────────────────────────────────────────────────────────────
export type FetchMethod = "rss" | "api" | "html";

export interface SourceHealth {
  last_fetch_at?: string | null;
  last_status?: string | null;
  error_count?: number;
  success_count?: number;
  [k: string]: unknown;
}

export interface Politeness {
  rps?: number;
  jitter_s?: number;
  max_concurrency?: number;
  respect_robots?: boolean;
  [k: string]: unknown;
}

export interface Source {
  id: number;
  name: string;
  homepage_url: string;
  feed_url?: string | null;
  api_kind?: string | null;
  fetch_method: FetchMethod;
  region?: string | null;
  languages: string[];
  categories: string[];
  bot_sensitivity: number;
  politeness: Politeness;
  robots_url?: string | null;
  enabled: boolean;
  health: SourceHealth;
}

export interface SourceCreate {
  name: string;
  homepage_url: string;
  feed_url?: string | null;
  api_kind?: string | null;
  fetch_method: FetchMethod;
  region?: string | null;
  languages?: string[];
  categories?: string[];
  bot_sensitivity?: number;
  politeness?: Politeness;
  robots_url?: string | null;
  enabled?: boolean;
}

export type SourceUpdate = Partial<SourceCreate> & { health?: SourceHealth };

// ── Articles ─────────────────────────────────────────────────────────────────
export interface EntityRef {
  id: number;
  name: string;
  type: string;
  salience: number;
  sentiment?: number | null;
}

export interface TopicRef {
  id: number;
  slug: string;
  label: string;
  confidence: number;
}

export interface Article {
  id: number;
  source_id: number;
  canonical_url: string;
  url: string;
  title: string;
  language?: string | null;
  authors: string[];
  published_at?: string | null;
  fetched_at: string;
  word_count: number;
  status: string;
  event_id?: number | null;
  body?: string | null;
  entities: EntityRef[];
  topics: TopicRef[];
  score?: number | null;
}

// ── Events ───────────────────────────────────────────────────────────────────
export interface EventArticleRef {
  id: number;
  title: string;
  source_id: number;
  language?: string | null;
  published_at?: string | null;
  similarity: number;
  is_seed: boolean;
}

export interface NewsEvent {
  id: number;
  title: string;
  summary?: string | null;
  started_at?: string | null;
  last_seen_at?: string | null;
  article_count: number;
  source_count: number;
  language_count: number;
  score: number;
  articles: EventArticleRef[];
}

// ── Trends / issues ──────────────────────────────────────────────────────────
export type TargetType = "entity" | "topic" | "keyword";

export interface TrendPoint {
  bucket: string;
  count: number;
  source_count: number;
  velocity: number;
  zscore: number;
}

export interface TrendSeries {
  target_type: string;
  target_id: number;
  label: string;
  points: TrendPoint[];
}

export interface Issue {
  target_type: string; // entity | topic | keyword
  target_id: number;
  label: string;
  score: number;
  window_start: string;
  window_end: string;
  mention_count: number;
  velocity: number;
  supporting_article_ids: number[];
  supporting_event_ids: number[];
}

// ── Reports ──────────────────────────────────────────────────────────────────
export interface ReportQuery {
  keywords?: string[];
  sector?: string | null;
  region?: string | null;
  window?: number | null;
  [k: string]: unknown;
}

export interface Report {
  id: number;
  query: ReportQuery;
  title: string;
  body_md: string;
  citations: Record<string, unknown>;
  provider?: string | null;
  model?: string | null;
  scheduled: boolean;
  version: number;
  created_at?: string | null;
}

// ── Search / report requests ─────────────────────────────────────────────────
export type SearchMode = "fts" | "semantic" | "hybrid";

export interface SearchRequest {
  q: string;
  mode?: SearchMode;
  window?: number | null;
  limit?: number;
  source_id?: number | null;
  language?: string | null;
  topic_id?: number | null;
}

export interface ReportRequest {
  keywords?: string[];
  sector?: string | null;
  region?: string | null;
  window?: number | null;
}

// ── Meta / streaming ─────────────────────────────────────────────────────────
export interface HealthStatus {
  status: string;
  service: string;
  version: string;
}

export interface IngestStats {
  type?: string;
  articles: number;
  events: number;
  sources: number;
  enabled_sources: number;
}
