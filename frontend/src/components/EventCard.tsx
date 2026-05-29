import { Globe, Languages, Newspaper, TrendingUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { NewsEvent } from "@/lib/types";
import { formatInt, timeAgo } from "@/lib/utils";

export function EventCard({ event }: { event: NewsEvent }) {
  const score = event.score ?? 0;
  const hot = score >= 7;
  return (
    <Card className="group animate-fade-in transition-colors hover:border-primary/40">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <CardTitle className="text-base leading-snug">{event.title}</CardTitle>
          <Badge variant={hot ? "warning" : "muted"} className="shrink-0 gap-1">
            <TrendingUp className="h-3 w-3" />
            {score.toFixed(1)}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 pt-0">
        {event.summary && <p className="line-clamp-2 text-sm text-muted-foreground">{event.summary}</p>}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1">
            <Newspaper className="h-3.5 w-3.5" /> {formatInt(event.article_count)} articles
          </span>
          <span className="inline-flex items-center gap-1">
            <Globe className="h-3.5 w-3.5" /> {event.source_count} sources
          </span>
          <span className="inline-flex items-center gap-1">
            <Languages className="h-3.5 w-3.5" /> {event.language_count} langs
          </span>
          <span className="ml-auto">{timeAgo(event.last_seen_at)}</span>
        </div>
      </CardContent>
    </Card>
  );
}
