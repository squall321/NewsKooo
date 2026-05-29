import { Activity, Radio, Trash2, Zap } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { EmptyState } from "@/components/states";
import { useIssueStream, type StreamStatus } from "@/hooks/useIssueStream";
import type { Issue } from "@/lib/types";
import { cn, formatSigned, timeAgo } from "@/lib/utils";

const statusMeta: Record<StreamStatus, { label: string; variant: "success" | "warning" | "muted" | "default"; pulse: boolean }> = {
  open: { label: "Live", variant: "success", pulse: true },
  connecting: { label: "Connecting", variant: "warning", pulse: false },
  reconnecting: { label: "Reconnecting", variant: "warning", pulse: false },
  mock: { label: "Live (mock)", variant: "default", pulse: true },
  closed: { label: "Paused", variant: "muted", pulse: false },
};

function targetVariant(score: number) {
  if (score >= 4) return "destructive" as const;
  if (score >= 3) return "warning" as const;
  return "default" as const;
}

export function StreamStatusBadge({ status }: { status: StreamStatus }) {
  const meta = statusMeta[status];
  return (
    <Badge variant={meta.variant} className="gap-1.5">
      <span className={cn("relative flex h-2 w-2")}>
        {meta.pulse && (
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-current opacity-60" />
        )}
        <span className="relative inline-flex h-2 w-2 rounded-full bg-current" />
      </span>
      {meta.label}
    </Badge>
  );
}

export function IssueRow({ issue }: { issue: Issue }) {
  return (
    <div className="animate-fade-in rounded-lg border border-border/70 bg-card/40 p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate font-medium">{issue.label}</p>
          <p className="text-xs capitalize text-muted-foreground">
            {issue.target_type} · {timeAgo(issue.window_end)}
          </p>
        </div>
        <Badge variant={targetVariant(issue.score)} className="shrink-0 gap-1 tabular-nums">
          <Zap className="h-3 w-3" />
          {issue.score.toFixed(2)}
        </Badge>
      </div>
      <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1">
          <Activity className="h-3 w-3" /> {issue.mention_count} mentions
        </span>
        <span>velocity {formatSigned(issue.velocity)}</span>
        {issue.supporting_article_ids.length > 0 && (
          <span className="ml-auto">{issue.supporting_article_ids.length} sources</span>
        )}
      </div>
    </div>
  );
}

interface IssueFeedProps {
  enabled?: boolean;
  height?: number;
  showHeader?: boolean;
}

/** Live SSE-driven issue alert feed (subscribes to `/api/stream/issues`). */
export function IssueFeed({ enabled = true, height = 420, showHeader = true }: IssueFeedProps) {
  const { issues, status, clear } = useIssueStream(enabled);

  return (
    <div className="flex h-full flex-col">
      {showHeader && (
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Radio className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium">Live alerts</span>
            <StreamStatusBadge status={status} />
          </div>
          {issues.length > 0 && (
            <Button variant="ghost" size="sm" onClick={clear} className="text-muted-foreground">
              <Trash2 className="h-3.5 w-3.5" /> Clear
            </Button>
          )}
        </div>
      )}
      <ScrollArea className="flex-1 pr-3" style={{ height }}>
        {issues.length === 0 ? (
          <EmptyState
            icon={Radio}
            title="Listening for issues…"
            description="Emerging-issue alerts will stream in here as the engine detects them."
          />
        ) : (
          <div className="space-y-2">
            {issues.map((issue, i) => (
              <IssueRow key={`${issue.target_type}:${issue.target_id}:${i}`} issue={issue} />
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
