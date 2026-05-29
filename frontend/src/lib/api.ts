/**
 * Typed fetch client for the NewsKoo FastAPI backend.
 *
 * Design:
 *  - One `request()` helper does fetch + JSON + error handling.
 *  - Every method has a `mock` counterpart. When `USE_MOCKS` is set (env), the
 *    mock is returned directly. Otherwise the live call runs and, on ANY failure
 *    (network error, non-2xx), transparently falls back to the mock so the UI
 *    stays usable when the backend is offline. The fallback is signalled via a
 *    one-shot console warning + the `apiMode` store so the UI can badge it.
 */
import * as mocks from "./mocks";
import type {
  Article,
  HealthStatus,
  IngestStats,
  Issue,
  NewsEvent,
  Paginated,
  Report,
  ReportRequest,
  SearchRequest,
  Source,
  SourceCreate,
  SourceUpdate,
  TargetType,
  TrendSeries,
} from "./types";

export const API_BASE = (import.meta.env.VITE_API_BASE ?? "http://localhost:8000").replace(/\/$/, "");
export const USE_MOCKS = String(import.meta.env.VITE_USE_MOCKS ?? "false").toLowerCase() === "true";

/** Reactive-ish flag: did at least one live call fall back to mocks? */
type ModeListener = (offline: boolean) => void;
let _offline = USE_MOCKS;
const _listeners = new Set<ModeListener>();
export function getOffline() {
  return _offline;
}
export function onModeChange(fn: ModeListener) {
  _listeners.add(fn);
  return () => _listeners.delete(fn);
}
function setOffline(v: boolean) {
  if (_offline === v) return;
  _offline = v;
  _listeners.forEach((l) => l(v));
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface RequestOpts {
  method?: string;
  body?: unknown;
  signal?: AbortSignal;
  query?: Record<string, string | number | boolean | null | undefined>;
}

function buildUrl(path: string, query?: RequestOpts["query"]): string {
  const url = new URL(API_BASE + path);
  if (query) {
    for (const [k, v] of Object.entries(query)) {
      if (v !== null && v !== undefined && v !== "") url.searchParams.set(k, String(v));
    }
  }
  return url.toString();
}

async function request<T>(path: string, opts: RequestOpts = {}): Promise<T> {
  const res = await fetch(buildUrl(path, opts.query), {
    method: opts.method ?? "GET",
    headers: opts.body !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
    signal: opts.signal,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = (data?.detail as string) ?? detail;
    } catch {
      /* ignore non-json error bodies */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

/**
 * Run a live call, falling back to a mock on failure.
 * - If USE_MOCKS: skip the network entirely.
 * - On success: mark online.
 * - On failure: warn once, mark offline, return the mock.
 */
async function withFallback<T>(label: string, live: () => Promise<T>, mock: () => T): Promise<T> {
  if (USE_MOCKS) return mock();
  try {
    const out = await live();
    setOffline(false);
    return out;
  } catch (err) {
    if (!_offline) {
      console.warn(
        `[NewsKoo] live API call "${label}" failed — serving mock data. Backend offline?`,
        err,
      );
    }
    setOffline(true);
    return mock();
  }
}

// ── Meta ─────────────────────────────────────────────────────────────────────
export const api = {
  health: () =>
    withFallback<HealthStatus>(
      "health",
      () => request<HealthStatus>("/health"),
      () => ({ status: "ok", service: "newskoo-api (mock)", version: "0.1.0" }),
    ),

  metrics: () => request<string>("/metrics"),

  // ── Sources ────────────────────────────────────────────────────────────────
  listSources: (params: {
    enabled?: boolean;
    region?: string;
    category?: string;
    limit?: number;
    offset?: number;
  } = {}) =>
    withFallback<Paginated<Source>>(
      "listSources",
      () => request<Paginated<Source>>("/api/sources", { query: params }),
      () => mocks.pageSources(params),
    ),

  getSource: (id: number) =>
    withFallback<Source>(
      "getSource",
      () => request<Source>(`/api/sources/${id}`),
      () => mocks.mockSources.find((s) => s.id === id) ?? mocks.mockSources[0],
    ),

  createSource: (payload: SourceCreate) =>
    request<Source>("/api/sources", { method: "POST", body: payload }),

  updateSource: (id: number, payload: SourceUpdate) =>
    request<Source>(`/api/sources/${id}`, { method: "PATCH", body: payload }),

  enableSource: (id: number) =>
    withFallback<Source>(
      "enableSource",
      () => request<Source>(`/api/sources/${id}/enable`, { method: "POST" }),
      () => ({ ...(mocks.mockSources.find((s) => s.id === id) ?? mocks.mockSources[0]), enabled: true }),
    ),

  disableSource: (id: number) =>
    withFallback<Source>(
      "disableSource",
      () => request<Source>(`/api/sources/${id}/disable`, { method: "POST" }),
      () => ({ ...(mocks.mockSources.find((s) => s.id === id) ?? mocks.mockSources[0]), enabled: false }),
    ),

  // ── Articles ─────────────────────────────────────────────────────────────────
  listArticles: (params: {
    source_id?: number;
    language?: string;
    since?: string;
    until?: string;
    limit?: number;
    offset?: number;
  } = {}) =>
    withFallback<Paginated<Article>>(
      "listArticles",
      () => request<Paginated<Article>>("/api/articles", { query: params }),
      () => mocks.pageArticles(params),
    ),

  recentArticles: (limit = 50) =>
    withFallback<Article[]>(
      "recentArticles",
      () => request<Article[]>("/api/articles/recent", { query: { limit } }),
      () => mocks.mockArticles.slice(0, limit),
    ),

  getArticle: (id: number) =>
    withFallback<Article>(
      "getArticle",
      () => request<Article>(`/api/articles/${id}`),
      () => mocks.mockArticles.find((a) => a.id === id) ?? mocks.mockArticles[0],
    ),

  // ── Events ───────────────────────────────────────────────────────────────────
  listEvents: (params: { order?: "score" | "recent"; limit?: number; offset?: number } = {}) =>
    withFallback<Paginated<NewsEvent>>(
      "listEvents",
      () => request<Paginated<NewsEvent>>("/api/events", { query: params }),
      () => ({
        items: mocks.mockEvents.slice(0, params.limit ?? 50),
        total: mocks.mockEvents.length,
        limit: params.limit ?? 50,
        offset: params.offset ?? 0,
      }),
    ),

  getEvent: (id: number) =>
    withFallback<NewsEvent>(
      "getEvent",
      () => request<NewsEvent>(`/api/events/${id}`),
      () => mocks.mockEvents.find((e) => e.id === id) ?? mocks.mockEvents[0],
    ),

  // ── Search ───────────────────────────────────────────────────────────────────
  search: (req: SearchRequest) =>
    withFallback<Article[]>(
      "search",
      () => request<Article[]>("/api/search", { method: "POST", body: req }),
      () => mocks.searchArticles(req),
    ),

  // ── Trends ───────────────────────────────────────────────────────────────────
  getTrend: (params: { target_type: TargetType; target_id?: number; keyword?: string; window?: number }) =>
    withFallback<TrendSeries>(
      "getTrend",
      () => request<TrendSeries>("/api/trends", { query: params }),
      () => mocks.mockTrendSeries(params.target_type, params.target_id ?? 11),
    ),

  topTrends: (params: { metric?: "velocity" | "zscore"; target_type?: TargetType; window?: number; limit?: number } = {}) =>
    withFallback<TrendSeries[]>(
      "topTrends",
      () => request<TrendSeries[]>("/api/trends/top", { query: params }),
      () => mocks.mockTopTrends(params.target_type),
    ),

  // ── Issues ───────────────────────────────────────────────────────────────────
  listIssues: (params: { threshold?: number; window?: number; limit?: number } = {}) =>
    withFallback<Issue[]>(
      "listIssues",
      () => request<Issue[]>("/api/issues", { query: params }),
      () => mocks.mockIssues,
    ),

  issuesForTarget: (target: string, params: { window?: number; limit?: number } = {}) =>
    withFallback<Issue[]>(
      "issuesForTarget",
      () => request<Issue[]>(`/api/issues/${target}`, { query: params }),
      () => mocks.mockIssues.filter((i) => `${i.target_type}:${i.target_id}` === target),
    ),

  // ── Reports ──────────────────────────────────────────────────────────────────
  listReports: (params: { limit?: number; offset?: number } = {}) =>
    withFallback<Paginated<Report>>(
      "listReports",
      () => request<Paginated<Report>>("/api/reports", { query: params }),
      () => ({
        items: mocks.mockReports.slice(0, params.limit ?? 50),
        total: mocks.mockReports.length,
        limit: params.limit ?? 50,
        offset: params.offset ?? 0,
      }),
    ),

  getReport: (id: number) =>
    withFallback<Report>(
      "getReport",
      () => request<Report>(`/api/reports/${id}`),
      () => mocks.mockReports.find((r) => r.id === id) ?? mocks.mockReports[0],
    ),

  generateReport: (req: ReportRequest) =>
    withFallback<Report>(
      "generateReport",
      () => request<Report>("/api/reports/generate", { method: "POST", body: req }),
      () => mocks.generateReport(req),
    ),
};

// ── Stats (for the dashboard; live WS path lives in the hook) ─────────────────
export function mockStatsSnapshot(): IngestStats {
  return mocks.mockStats;
}

/** Absolute URL of the issue SSE stream. */
export function issueStreamUrl(): string {
  return buildUrl("/api/stream/issues");
}

/** WebSocket URL for live stats. */
export function statsWsUrl(): string {
  return API_BASE.replace(/^http/, "ws") + "/api/ws/stats";
}
