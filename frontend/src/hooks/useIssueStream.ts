import * as React from "react";
import { issueStreamUrl, USE_MOCKS, getOffline } from "@/lib/api";
import { mockLiveIssue } from "@/lib/mocks";
import type { Issue } from "@/lib/types";

export type StreamStatus = "connecting" | "open" | "reconnecting" | "mock" | "closed";

interface UseIssueStreamResult {
  issues: Issue[];
  status: StreamStatus;
  clear: () => void;
}

const MAX_BUFFER = 100;

/**
 * Subscribe to the backend SSE issue stream (`GET /api/stream/issues`) via
 * EventSource, with automatic exponential-backoff reconnect.
 *
 * Behaviour:
 *  - The backend emits `event: issue` (JSON IssueAlert) and `event: heartbeat`.
 *  - On open → status "open"; on error → EventSource auto-reconnects, we surface
 *    "reconnecting" and apply our own capped backoff on top for hard failures.
 *  - When VITE_USE_MOCKS is set, or the api layer is already in offline/mock
 *    mode, we synthesize a periodic mock alert instead so the feed stays alive.
 */
export function useIssueStream(enabled = true): UseIssueStreamResult {
  const [issues, setIssues] = React.useState<Issue[]>([]);
  const [status, setStatus] = React.useState<StreamStatus>("connecting");

  const push = React.useCallback((issue: Issue) => {
    setIssues((prev) => [issue, ...prev].slice(0, MAX_BUFFER));
  }, []);

  const clear = React.useCallback(() => setIssues([]), []);

  React.useEffect(() => {
    if (!enabled) {
      setStatus("closed");
      return;
    }

    // ── Mock path ──────────────────────────────────────────────────────────
    if (USE_MOCKS || getOffline()) {
      setStatus("mock");
      let seq = 0;
      // Seed a couple immediately so the feed isn't empty.
      push(mockLiveIssue(seq++));
      push(mockLiveIssue(seq++));
      const id = window.setInterval(() => push(mockLiveIssue(seq++)), 6000);
      return () => window.clearInterval(id);
    }

    // ── Live SSE path with reconnect ────────────────────────────────────────
    let es: EventSource | null = null;
    let retry = 0;
    let reconnectTimer: number | undefined;
    let stopped = false;

    const connect = () => {
      if (stopped) return;
      setStatus(retry === 0 ? "connecting" : "reconnecting");
      es = new EventSource(issueStreamUrl());

      es.onopen = () => {
        retry = 0;
        setStatus("open");
      };

      es.addEventListener("issue", (ev) => {
        try {
          const data = JSON.parse((ev as MessageEvent).data) as Issue;
          push(data);
        } catch {
          /* ignore malformed payloads */
        }
      });

      // heartbeats keep the connection warm; nothing to render.
      es.addEventListener("heartbeat", () => {});

      es.onerror = () => {
        // EventSource will retry on its own, but if the connection is fully
        // closed we drive a capped backoff reconnect ourselves.
        if (es && es.readyState === EventSource.CLOSED) {
          es.close();
          es = null;
          if (stopped) return;
          setStatus("reconnecting");
          const delay = Math.min(1000 * 2 ** retry, 15000);
          retry += 1;
          reconnectTimer = window.setTimeout(connect, delay);
        } else {
          setStatus("reconnecting");
        }
      };
    };

    connect();

    return () => {
      stopped = true;
      if (reconnectTimer) window.clearTimeout(reconnectTimer);
      es?.close();
    };
  }, [enabled, push]);

  return { issues, status, clear };
}
