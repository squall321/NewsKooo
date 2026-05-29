import { ExternalLink, Hash } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/states";
import type { Article } from "@/lib/types";
import { timeAgo } from "@/lib/utils";

interface ArticleListProps {
  articles: Article[];
  showScore?: boolean;
  sourceName?: (id: number) => string;
}

export function ArticleList({ articles, showScore, sourceName }: ArticleListProps) {
  if (!articles.length) {
    return <EmptyState title="No articles" description="Nothing matched the current filters." />;
  }
  return (
    <ul className="divide-y divide-border/70">
      {articles.map((a) => (
        <li key={a.id} className="animate-fade-in py-3 first:pt-0">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <a
                href={a.url}
                target="_blank"
                rel="noreferrer"
                className="group inline-flex items-start gap-1.5 font-medium leading-snug hover:text-primary"
              >
                <span className="line-clamp-2">{a.title}</span>
                <ExternalLink className="mt-0.5 h-3.5 w-3.5 shrink-0 opacity-0 transition-opacity group-hover:opacity-60" />
              </a>
              <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                <span>{sourceName ? sourceName(a.source_id) : `source #${a.source_id}`}</span>
                {a.language && <span className="uppercase">{a.language}</span>}
                <span>{timeAgo(a.published_at ?? a.fetched_at)}</span>
                {a.word_count > 0 && <span>{a.word_count.toLocaleString()} words</span>}
              </div>
              {a.topics.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {a.topics.slice(0, 3).map((t) => (
                    <Badge key={t.id} variant="secondary" className="gap-1 text-[10px]">
                      <Hash className="h-2.5 w-2.5" />
                      {t.label}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
            {showScore && a.score != null && (
              <Badge variant="outline" className="shrink-0 tabular-nums">
                {a.score.toFixed(3)}
              </Badge>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}
