# NewsKoo Frontend

React 18 + TypeScript + Vite SPA. **Phase 8** — the operator-facing UI for the
NewsKoo news-intelligence platform. Dark-mode-first, modern, and resilient: it
runs and looks good even when the backend is offline.

## Stack

- **React 18 + TypeScript (strict)** on **Vite 5**
- **Tailwind CSS** + a **shadcn/ui-style** component layer (Radix primitives + `cva`)
- **TanStack Query** (server state) · **TanStack Table** (Sources grid)
- **Recharts** (trend / velocity / z-score charts)
- **Zustand** (client UI state) · **React Router** (routing) · **lucide-react** (icons)
- **react-markdown + remark-gfm** (report rendering) · **sonner** (toasts)

## Pages

| Route       | View      | What it shows |
|-------------|-----------|---------------|
| `/`         | Dashboard | Live ingestion stats (WS), top trend signal, top movers, top events, live issue feed |
| `/search`   | Search    | Mode toggle (fts / semantic / hybrid) + time window, ranked results |
| `/trends`   | Trends    | Pick entity/topic/keyword, volume/velocity/z-score charts, top movers |
| `/issues`   | Issues    | Live SSE alert stream + current (last-24h) anomalies |
| `/reports`  | Reports   | List + markdown viewer + a generate form |
| `/sources`  | Sources   | TanStack Table with enable/disable and region/category/status filters |

## Data layer

- `src/lib/types.ts` — wire types mirroring the FastAPI `api/schemas.py`.
- `src/lib/api.ts` — a single typed `fetch` client for **every** `/api/*`
  endpoint, plus `/health`, `/metrics`, and URL builders for the SSE/WS streams.
- `src/lib/mocks.ts` — realistic, deterministic mock data + a mock for each call.
- `src/lib/query.ts` — the shared `QueryClient`.

### Mock fallback (`VITE_USE_MOCKS`)

The app works offline. Each API method wraps a live call with `withFallback`:

- `VITE_USE_MOCKS=true` → mocks are served directly (no network).
- Otherwise → the live call runs; on **any** failure (network error / non-2xx)
  it transparently returns the matching mock and flips an internal "offline"
  flag. The top bar shows an **"Offline — mock data"** badge so it's never silent.

### Live streaming

- **Issues** — `useIssueStream` opens an `EventSource` to
  `GET /api/stream/issues`, listening for `event: issue` (JSON `IssueAlert`) and
  `event: heartbeat`. It reconnects with capped exponential backoff. When mocks
  are active (forced or fallback) it synthesizes a periodic alert so the feed
  stays live. Status is surfaced as a pulsing Live / Reconnecting badge.
- **Stats** — `useStatsStream` connects to the `WS /api/ws/stats` socket
  (pushes counts every ~5s), with the same backoff + mock fallback.

## Configuration

Copy `.env.example` → `.env` and adjust:

```bash
VITE_API_BASE=http://localhost:8000   # backend base URL (no trailing slash)
VITE_USE_MOCKS=false                  # "true" to force mock data
```

## Scripts

```bash
npm install
npm run dev        # Vite dev server → http://localhost:5173
npm run build      # tsc -b && vite build  (strict typecheck + production bundle)
npm run preview    # preview the production build → http://localhost:4173
npm run lint       # ESLint
npm run typecheck  # tsc -b --noEmit
```
