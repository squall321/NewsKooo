import * as React from "react";
import { statsWsUrl, USE_MOCKS, getOffline } from "@/lib/api";
import { mockStats } from "@/lib/mocks";
import type { IngestStats } from "@/lib/types";

export type WsStatus = "connecting" | "open" | "reconnecting" | "mock" | "closed";

/**
 * Live ingestion stats over the `/api/ws/stats` WebSocket (pushes every ~5s).
 * Reconnects with capped backoff; falls back to a gently-incrementing mock
 * snapshot when mocks are enabled or the backend is unreachable.
 */
export function useStatsStream(enabled = true): { stats: IngestStats | null; status: WsStatus } {
  const [stats, setStats] = React.useState<IngestStats | null>(null);
  const [status, setStatus] = React.useState<WsStatus>("connecting");

  React.useEffect(() => {
    if (!enabled) {
      setStatus("closed");
      return;
    }

    if (USE_MOCKS || getOffline()) {
      setStatus("mock");
      let tick = 0;
      const apply = () =>
        setStats({
          ...mockStats,
          articles: mockStats.articles + tick * 7,
          events: mockStats.events + Math.floor(tick / 3),
        });
      apply();
      const id = window.setInterval(() => {
        tick += 1;
        apply();
      }, 5000);
      return () => window.clearInterval(id);
    }

    let ws: WebSocket | null = null;
    let retry = 0;
    let timer: number | undefined;
    let stopped = false;

    const connect = () => {
      if (stopped) return;
      setStatus(retry === 0 ? "connecting" : "reconnecting");
      try {
        ws = new WebSocket(statsWsUrl());
      } catch {
        scheduleReconnect();
        return;
      }

      ws.onopen = () => {
        retry = 0;
        setStatus("open");
      };
      ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data) as IngestStats & { type?: string };
          if (data.type === "stats" || "articles" in data) setStats(data);
        } catch {
          /* ignore */
        }
      };
      ws.onerror = () => ws?.close();
      ws.onclose = () => {
        if (!stopped) scheduleReconnect();
      };
    };

    const scheduleReconnect = () => {
      if (stopped) return;
      setStatus("reconnecting");
      const delay = Math.min(1000 * 2 ** retry, 15000);
      retry += 1;
      timer = window.setTimeout(connect, delay);
    };

    connect();
    return () => {
      stopped = true;
      if (timer) window.clearTimeout(timer);
      ws?.close();
    };
  }, [enabled]);

  return { stats, status };
}
