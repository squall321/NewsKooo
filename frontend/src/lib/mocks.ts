/**
 * Realistic mock data + a mock implementation of every API operation.
 *
 * Used in two situations:
 *  1. VITE_USE_MOCKS=true — every call is served from here (offline demo).
 *  2. Any live request fails (backend offline) — the api client falls back to
 *     the matching mock so the UI keeps working and looks good.
 *
 * Data is deterministic (seeded) so charts/lists are stable across renders.
 */
import { seededRandom } from "./utils";
import type {
  Article,
  Issue,
  NewsEvent,
  Paginated,
  Report,
  Security,
  Signal,
  SignalDirection,
  Source,
  TrendPoint,
  TrendSeries,
  SearchRequest,
  IngestStats,
  ReportRequest,
} from "./types";

const now = Date.now();
const hoursAgo = (h: number) => new Date(now - h * 3600_000).toISOString();
const minutesAgo = (m: number) => new Date(now - m * 60_000).toISOString();

// ── Sources ──────────────────────────────────────────────────────────────────
const SOURCE_DEFS: Array<Partial<Source> & Pick<Source, "name" | "fetch_method">> = [
  { name: "Reuters World", fetch_method: "rss", region: "global", languages: ["en"], categories: ["world", "business"], homepage_url: "https://www.reuters.com", feed_url: "https://www.reuters.com/rssfeed/world" },
  { name: "Associated Press", fetch_method: "rss", region: "us", languages: ["en"], categories: ["world", "politics"], homepage_url: "https://apnews.com", feed_url: "https://apnews.com/rss" },
  { name: "GDELT Global", fetch_method: "api", api_kind: "gdelt", region: "global", languages: ["en", "es", "fr", "de"], categories: ["world"], homepage_url: "https://www.gdeltproject.org" },
  { name: "arXiv cs.AI", fetch_method: "rss", region: "global", languages: ["en"], categories: ["science", "tech"], homepage_url: "https://arxiv.org", feed_url: "https://export.arxiv.org/rss/cs.AI" },
  { name: "Nature News", fetch_method: "rss", region: "global", languages: ["en"], categories: ["science"], homepage_url: "https://www.nature.com", feed_url: "https://www.nature.com/nature.rss" },
  { name: "Nikkei Asia", fetch_method: "html", region: "jp", languages: ["en", "ja"], categories: ["business", "asia"], homepage_url: "https://asia.nikkei.com", bot_sensitivity: 2 },
  { name: "Le Monde", fetch_method: "rss", region: "fr", languages: ["fr"], categories: ["world", "politics"], homepage_url: "https://www.lemonde.fr", feed_url: "https://www.lemonde.fr/rss/une.xml" },
  { name: "Der Spiegel", fetch_method: "rss", region: "de", languages: ["de"], categories: ["world", "politics"], homepage_url: "https://www.spiegel.de", feed_url: "https://www.spiegel.de/schlagzeilen/index.rss" },
  { name: "TechCrunch", fetch_method: "rss", region: "us", languages: ["en"], categories: ["tech", "startups"], homepage_url: "https://techcrunch.com", feed_url: "https://techcrunch.com/feed/" },
  { name: "EurekAlert!", fetch_method: "rss", region: "global", languages: ["en"], categories: ["science"], homepage_url: "https://www.eurekalert.org", feed_url: "https://www.eurekalert.org/rss.xml" },
  { name: "Bloomberg Markets", fetch_method: "html", region: "us", languages: ["en"], categories: ["business", "markets"], homepage_url: "https://www.bloomberg.com", bot_sensitivity: 3 },
  { name: "South China Morning Post", fetch_method: "rss", region: "hk", languages: ["en", "zh"], categories: ["asia", "business"], homepage_url: "https://www.scmp.com", feed_url: "https://www.scmp.com/rss/91/feed" },
];

export const mockSources: Source[] = SOURCE_DEFS.map((d, i) => {
  const rnd = seededRandom(i + 7);
  return {
    id: i + 1,
    name: d.name,
    homepage_url: d.homepage_url ?? `https://example-${i}.com`,
    feed_url: d.feed_url ?? null,
    api_kind: d.api_kind ?? null,
    fetch_method: d.fetch_method,
    region: d.region ?? null,
    languages: d.languages ?? ["en"],
    categories: d.categories ?? ["world"],
    bot_sensitivity: d.bot_sensitivity ?? 0,
    politeness: { rps: 0.5, jitter_s: 0.5, max_concurrency: 2, respect_robots: true },
    robots_url: null,
    enabled: i % 7 !== 5,
    health: {
      last_fetch_at: minutesAgo(Math.floor(rnd() * 120)),
      last_status: rnd() > 0.15 ? "ok" : "error",
      success_count: Math.floor(rnd() * 5000),
      error_count: Math.floor(rnd() * 40),
    },
  };
});

// ── Headlines for articles / events ──────────────────────────────────────────
const HEADLINES = [
  "Central banks signal coordinated pause as inflation data cools",
  "Breakthrough solid-state battery hits 500-mile range in lab trials",
  "Chipmaker unveils 2nm process, reshaping supply chain economics",
  "Pacific trade bloc expands membership amid shifting alliances",
  "New mRNA platform shows promise against resistant pathogens",
  "Quantum error-correction milestone narrows gap to fault tolerance",
  "Energy grid operators warn of strain from data-center boom",
  "Rare-earth refining venture aims to cut import dependence",
  "Autonomous shipping corridor opens between two major ports",
  "Gene-editing therapy receives accelerated regulatory review",
  "Satellite constellation reaches global low-latency coverage",
  "Fusion startup reports net-energy-positive shot, awaiting peer review",
];

const LANGS = ["en", "en", "en", "fr", "de", "ja", "zh", "es"];

export const mockArticles: Article[] = Array.from({ length: 48 }, (_, i) => {
  const rnd = seededRandom(i * 13 + 1);
  const src = mockSources[i % mockSources.length];
  const title = HEADLINES[i % HEADLINES.length];
  return {
    id: 1000 + i,
    source_id: src.id,
    canonical_url: `https://news.example.com/a/${1000 + i}`,
    url: `https://news.example.com/a/${1000 + i}?utm=feed`,
    title: `${title}`,
    language: LANGS[i % LANGS.length],
    authors: rnd() > 0.5 ? ["Staff Reporter"] : ["A. Correspondent", "B. Analyst"],
    published_at: hoursAgo(Math.floor(rnd() * 72)),
    fetched_at: hoursAgo(Math.floor(rnd() * 70)),
    word_count: 300 + Math.floor(rnd() * 1400),
    status: "analyzed",
    event_id: i % 4 === 0 ? 2000 + (i % 6) : null,
    body:
      `## ${title}\n\n` +
      "In a development closely watched by analysts, sources indicate the situation is evolving rapidly. " +
      "Multiple outlets across regions corroborate the core facts, while interpretation of the longer-term impact varies.\n\n" +
      "Observers note that the velocity of related coverage has accelerated over the past 24 hours, a pattern NewsKoo's issue engine flags as an emerging signal.\n\n" +
      "> \"This is the kind of cross-source convergence we monitor for,\" one market strategist said.\n\n" +
      "Further reporting is expected as the story develops.",
    entities: [
      { id: 1, name: "Federal Reserve", type: "ORG", salience: 0.4 + rnd() * 0.5, sentiment: rnd() - 0.5 },
      { id: 2, name: "Taiwan", type: "GPE", salience: 0.2 + rnd() * 0.4, sentiment: rnd() - 0.5 },
    ],
    topics: [
      { id: 10, slug: "macro", label: "Macroeconomics", confidence: 0.6 + rnd() * 0.3 },
      { id: 11, slug: "semiconductors", label: "Semiconductors", confidence: 0.4 + rnd() * 0.4 },
    ],
    score: null,
  };
});

// ── Events ───────────────────────────────────────────────────────────────────
export const mockEvents: NewsEvent[] = Array.from({ length: 9 }, (_, i) => {
  const rnd = seededRandom(i * 29 + 3);
  const members = mockArticles.slice(i * 3, i * 3 + 4 + Math.floor(rnd() * 3));
  return {
    id: 2000 + i,
    title: HEADLINES[i % HEADLINES.length],
    summary:
      "Cross-source clustering linked coverage from multiple regions into a single developing story, with sentiment skewing cautious as new details emerge.",
    started_at: hoursAgo(48 - i * 2),
    last_seen_at: hoursAgo(Math.floor(rnd() * 6)),
    article_count: members.length,
    source_count: new Set(members.map((m) => m.source_id)).size,
    language_count: new Set(members.map((m) => m.language)).size,
    score: Number((9.5 - i * 0.7 + rnd()).toFixed(2)),
    articles: members.map((m, j) => ({
      id: m.id,
      title: m.title,
      source_id: m.source_id,
      language: m.language ?? null,
      published_at: m.published_at ?? null,
      similarity: Number((0.95 - j * 0.06).toFixed(3)),
      is_seed: j === 0,
    })),
  };
});

// ── Trends ───────────────────────────────────────────────────────────────────
const TREND_LABELS: Array<{ id: number; type: string; label: string }> = [
  { id: 11, type: "topic", label: "Semiconductors" },
  { id: 1, type: "entity", label: "Federal Reserve" },
  { id: 12, type: "topic", label: "Fusion Energy" },
  { id: 2, type: "entity", label: "Taiwan" },
  { id: 13, type: "topic", label: "mRNA Therapeutics" },
  { id: 3, type: "entity", label: "Nvidia" },
  { id: 14, type: "keyword", label: "solid-state battery" },
  { id: 15, type: "keyword", label: "rare earth" },
];

function buildPoints(seed: number, buckets: number, spike: boolean): TrendPoint[] {
  const rnd = seededRandom(seed);
  const pts: TrendPoint[] = [];
  let prev = 5 + Math.floor(rnd() * 10);
  for (let b = buckets - 1; b >= 0; b--) {
    const base = 5 + Math.floor(rnd() * 12);
    const surge = spike && b < 4 ? (4 - b) * (8 + rnd() * 14) : 0;
    const count = Math.max(0, Math.round(base + surge));
    const velocity = count - prev;
    const zscore = spike && b < 3 ? 2.5 + rnd() * 3 : rnd() * 1.5 - 0.5;
    pts.push({
      bucket: hoursAgo(b * 6),
      count,
      source_count: 1 + Math.floor(rnd() * 6),
      velocity: Number(velocity.toFixed(2)),
      zscore: Number(zscore.toFixed(2)),
    });
    prev = count;
  }
  return pts;
}

export function mockTrendSeries(targetType: string, targetId: number): TrendSeries {
  const meta = TREND_LABELS.find((t) => t.id === targetId) ?? TREND_LABELS[0];
  return {
    target_type: targetType,
    target_id: targetId,
    label: meta.label,
    points: buildPoints(targetId * 17, 28, targetId % 3 === 0),
  };
}

export function mockTopTrends(targetType?: string): TrendSeries[] {
  return TREND_LABELS.filter((t) => !targetType || t.type === targetType).map((t, i) => ({
    target_type: t.type,
    target_id: t.id,
    label: t.label,
    points: [buildPoints(t.id * 17, 28, i % 2 === 0).at(-1)!],
  }));
}

// ── Issues ───────────────────────────────────────────────────────────────────
export const mockIssues: Issue[] = TREND_LABELS.slice(0, 6).map((t, i) => {
  const rnd = seededRandom(t.id * 5 + 1);
  return {
    target_type: t.type,
    target_id: t.id,
    label: t.label,
    score: Number((4.2 - i * 0.4 + rnd()).toFixed(2)),
    window_start: minutesAgo(60 + i * 15),
    window_end: minutesAgo(i * 15),
    mention_count: 18 + Math.floor(rnd() * 60),
    velocity: Number((6 + rnd() * 20).toFixed(2)),
    supporting_article_ids: mockArticles.slice(i * 2, i * 2 + 4).map((a) => a.id),
    supporting_event_ids: [2000 + (i % mockEvents.length)],
  };
});

/** A live-looking alert for the SSE mock stream. */
export function mockLiveIssue(seq: number): Issue {
  const t = TREND_LABELS[seq % TREND_LABELS.length];
  const rnd = seededRandom(seq * 101 + 7);
  return {
    target_type: t.type,
    target_id: t.id,
    label: t.label,
    score: Number((2.6 + rnd() * 2.5).toFixed(2)),
    window_start: minutesAgo(30),
    window_end: new Date().toISOString(),
    mention_count: 12 + Math.floor(rnd() * 40),
    velocity: Number((4 + rnd() * 18).toFixed(2)),
    supporting_article_ids: mockArticles.slice(0, 3).map((a) => a.id),
    supporting_event_ids: [2000 + (seq % mockEvents.length)],
  };
}

// ── Securities ───────────────────────────────────────────────────────────────
const SECURITY_DEFS: Array<Omit<Security, "id">> = [
  { symbol: "NVDA", name: "NVIDIA Corporation", exchange: "NASDAQ", country: "US", asset_class: "equity" },
  { symbol: "TSM", name: "Taiwan Semiconductor Mfg.", exchange: "NYSE", country: "TW", asset_class: "equity" },
  { symbol: "ASML", name: "ASML Holding N.V.", exchange: "AEX", country: "NL", asset_class: "equity" },
  { symbol: "AAPL", name: "Apple Inc.", exchange: "NASDAQ", country: "US", asset_class: "equity" },
  { symbol: "MSFT", name: "Microsoft Corporation", exchange: "NASDAQ", country: "US", asset_class: "equity" },
  { symbol: "005930.KS", name: "Samsung Electronics", exchange: "KRX", country: "KR", asset_class: "equity" },
  { symbol: "SOXX", name: "iShares Semiconductor ETF", exchange: "NASDAQ", country: "US", asset_class: "etf" },
  { symbol: "SPY", name: "SPDR S&P 500 ETF Trust", exchange: "ARCA", country: "US", asset_class: "etf" },
  { symbol: "BTC-USD", name: "Bitcoin / US Dollar", exchange: "CRYPTO", country: "—", asset_class: "crypto" },
  { symbol: "ETH-USD", name: "Ethereum / US Dollar", exchange: "CRYPTO", country: "—", asset_class: "crypto" },
  { symbol: "USDJPY", name: "US Dollar / Japanese Yen", exchange: "FX", country: "—", asset_class: "fx" },
  { symbol: "EURUSD", name: "Euro / US Dollar", exchange: "FX", country: "—", asset_class: "fx" },
  { symbol: "CL=F", name: "Crude Oil WTI Futures", exchange: "NYMEX", country: "US", asset_class: "commodity" },
  { symbol: "GC=F", name: "Gold Futures", exchange: "COMEX", country: "US", asset_class: "commodity" },
  { symbol: "US10Y", name: "US 10-Year Treasury Yield", exchange: "CBOT", country: "US", asset_class: "rate" },
];

export const mockSecurities: Security[] = SECURITY_DEFS.map((d, i) => ({ id: i + 1, ...d }));

// ── Signals ──────────────────────────────────────────────────────────────────
function directionFor(score: number): SignalDirection {
  if (score >= 0.15) return "bullish";
  if (score <= -0.15) return "bearish";
  return "neutral";
}

const SIGNAL_HORIZONS = [24, 72, 168];

/** Deterministic signal for a given security + sequence index (most recent first). */
function buildSignal(security: Security, seq: number): Signal {
  const rnd = seededRandom(security.id * 131 + seq * 7 + 1);
  // Center the score so a security trends one way, with noise per point.
  const bias = ((security.id % 5) - 2) / 4; // -0.5 .. 0.5
  const score = Math.max(-1, Math.min(1, Number((bias + (rnd() - 0.5) * 0.9).toFixed(3))));
  const magnitude = Number(Math.min(1, Math.abs(score) * 0.7 + rnd() * 0.35).toFixed(3));
  const confidence = Number((0.45 + rnd() * 0.5).toFixed(3));
  const nArticles = 2 + Math.floor(rnd() * 6);
  const nEvents = Math.floor(rnd() * 3);
  return {
    id: security.id * 1000 + seq,
    security_id: security.id,
    as_of: hoursAgo(seq * 6),
    horizon_hours: SIGNAL_HORIZONS[seq % SIGNAL_HORIZONS.length],
    score,
    direction: directionFor(score),
    magnitude,
    confidence,
    components: {
      sentiment: Number((score * 0.6 + (rnd() - 0.5) * 0.3).toFixed(3)),
      momentum: Number(((rnd() - 0.5) * 1.2).toFixed(3)),
      volume: Number((rnd()).toFixed(3)),
      novelty: Number((rnd()).toFixed(3)),
    },
    supporting_article_ids: mockArticles.slice(seq % 6, (seq % 6) + nArticles).map((a) => a.id),
    supporting_event_ids: Array.from({ length: nEvents }, (_, k) => 2000 + ((seq + k) % mockEvents.length)),
    created_at: hoursAgo(seq * 6),
  };
}

/** Full deterministic signal history per security, newest last (chart-friendly order). */
export const mockSignalHistory: Record<number, Signal[]> = Object.fromEntries(
  mockSecurities.map((sec) => [
    sec.id,
    Array.from({ length: 24 }, (_, seq) => buildSignal(sec, seq)).reverse(),
  ]),
);

/** Latest signal per security. */
export const mockSignals: Signal[] = mockSecurities.map((sec) => mockSignalHistory[sec.id].at(-1)!);

export function pageSecurities(opts: {
  q?: string;
  asset_class?: string;
  limit?: number;
  offset?: number;
}): Paginated<Security> {
  let items = mockSecurities.slice();
  if (opts.q) {
    const q = opts.q.toLowerCase();
    items = items.filter((s) => s.symbol.toLowerCase().includes(q) || s.name.toLowerCase().includes(q));
  }
  if (opts.asset_class) items = items.filter((s) => s.asset_class === opts.asset_class);
  const total = items.length;
  const offset = opts.offset ?? 0;
  const limit = opts.limit ?? 50;
  return { items: items.slice(offset, offset + limit), total, limit, offset };
}

export function pageSignals(opts: {
  security_id?: number;
  min_abs_score?: number;
  limit?: number;
  offset?: number;
}): Paginated<Signal> {
  let items = opts.security_id != null
    ? (mockSignalHistory[opts.security_id] ?? []).slice().reverse()
    : mockSignals.slice();
  if (opts.min_abs_score != null) items = items.filter((s) => Math.abs(s.score) >= opts.min_abs_score!);
  const total = items.length;
  const offset = opts.offset ?? 0;
  const limit = opts.limit ?? 50;
  return { items: items.slice(offset, offset + limit), total, limit, offset };
}

export function mockTopSignals(limit = 10): Signal[] {
  return mockSignals
    .slice()
    .sort((a, b) => Math.abs(b.score) - Math.abs(a.score))
    .slice(0, limit);
}

// ── Reports ──────────────────────────────────────────────────────────────────
const REPORT_BODY = `# Semiconductor Supply Chain — Weekly Signal Report

## Executive summary

Coverage velocity around **advanced-node manufacturing** rose sharply this week,
driven by a 2nm process announcement and renewed attention on rare-earth refining.
NewsKoo's issue engine flagged three above-threshold spikes across entities and
topics.

## Key signals

1. **2nm process economics** — multiple outlets converged within 18 hours
   (z-score 3.4). Sentiment cautiously positive on yield claims [^1].
2. **Rare-earth refining** — policy-driven coverage, accelerating velocity [^2].
3. **Data-center grid strain** — recurring secondary theme linking energy and
   compute [^3].

## Regional breakdown

| Region | Articles | Dominant angle |
|--------|----------|----------------|
| Asia   | 41       | Capacity, fabs |
| US     | 33       | Policy, demand |
| Europe | 19       | Supply security |

## Outlook

Expect continued elevation as earnings season approaches. Watch for cross-source
confirmation on yield figures before treating the 2nm claims as settled.

[^1]: Reuters World — "Chipmaker unveils 2nm process"
[^2]: Nikkei Asia — "Rare-earth refining venture"
[^3]: Bloomberg Markets — "Grid operators warn of strain"
`;

export const mockReports: Report[] = Array.from({ length: 5 }, (_, i) => ({
  id: 500 + i,
  query: {
    keywords: ["semiconductors", "rare earth", "2nm"],
    sector: i % 2 === 0 ? "technology" : "energy",
    region: i % 3 === 0 ? "asia" : null,
    window: 168,
  },
  title:
    i === 0
      ? "Semiconductor Supply Chain — Weekly Signal Report"
      : `Sector Signal Report #${500 + i}`,
  body_md: REPORT_BODY,
  citations: { "1": "art:1001", "2": "art:1004", "3": "art:1010" },
  provider: "anthropic",
  model: "claude-sonnet",
  scheduled: i % 2 === 1,
  version: 1,
  created_at: hoursAgo(i * 24 + 2),
}));

export const mockStats: IngestStats = {
  type: "stats",
  articles: 184_204,
  events: 12_488,
  sources: mockSources.length,
  enabled_sources: mockSources.filter((s) => s.enabled).length,
};

// ── Mock query helpers (mirror the api surface) ──────────────────────────────
export function pageSources(opts: {
  enabled?: boolean;
  region?: string;
  category?: string;
  limit?: number;
  offset?: number;
}): Paginated<Source> {
  let items = mockSources.slice();
  if (opts.enabled != null) items = items.filter((s) => s.enabled === opts.enabled);
  if (opts.region) items = items.filter((s) => s.region === opts.region);
  if (opts.category) items = items.filter((s) => s.categories.includes(opts.category!));
  const total = items.length;
  const offset = opts.offset ?? 0;
  const limit = opts.limit ?? 50;
  return { items: items.slice(offset, offset + limit), total, limit, offset };
}

export function pageArticles(opts: {
  source_id?: number;
  language?: string;
  limit?: number;
  offset?: number;
}): Paginated<Article> {
  let items = mockArticles.slice();
  if (opts.source_id != null) items = items.filter((a) => a.source_id === opts.source_id);
  if (opts.language) items = items.filter((a) => a.language === opts.language);
  const total = items.length;
  const offset = opts.offset ?? 0;
  const limit = opts.limit ?? 50;
  return { items: items.slice(offset, offset + limit), total, limit, offset };
}

export function searchArticles(req: SearchRequest): Article[] {
  const q = req.q.toLowerCase();
  const limit = req.limit ?? 20;
  const matched = mockArticles
    .filter((a) => !q || a.title.toLowerCase().includes(q) || (a.body ?? "").toLowerCase().includes(q))
    .slice(0, limit);
  const base = matched.length ? matched : mockArticles.slice(0, limit);
  return base.map((a, i) => ({
    ...a,
    score: Number((1 - i * (1 / Math.max(base.length, 1)) * 0.6).toFixed(4)),
  }));
}

export function generateReport(req: ReportRequest): Report {
  return {
    id: 999,
    query: {
      keywords: req.keywords ?? [],
      sector: req.sector ?? null,
      region: req.region ?? null,
      window: req.window ?? 168,
    },
    title: `Report — ${(req.keywords ?? ["topics"]).slice(0, 3).join(", ") || "topics"}`,
    body_md:
      `# Generated Report (mock)\n\n` +
      `**Keywords:** ${(req.keywords ?? []).join(", ") || "—"}  \n` +
      `**Sector:** ${req.sector ?? "—"}  \n` +
      `**Region:** ${req.region ?? "—"}  \n` +
      `**Window:** ${req.window ?? 168}h\n\n` +
      REPORT_BODY,
    citations: {},
    provider: "mock",
    model: "mock-1",
    scheduled: false,
    version: 1,
    created_at: new Date().toISOString(),
  };
}
