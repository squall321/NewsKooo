import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import { Search as SearchIcon, Sparkles, Type, Layers } from "lucide-react";
import { api } from "@/lib/api";
import { ArticleList } from "@/components/ArticleList";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { EmptyState, ErrorState, ListSkeleton } from "@/components/states";
import type { SearchMode } from "@/lib/types";

const MODES: { value: SearchMode; label: string; icon: React.ComponentType<{ className?: string }>; hint: string }[] = [
  { value: "hybrid", label: "Hybrid", icon: Layers, hint: "Lexical + semantic, fused (RRF)" },
  { value: "fts", label: "Full-text", icon: Type, hint: "PostgreSQL FTS ranking" },
  { value: "semantic", label: "Semantic", icon: Sparkles, hint: "pgvector cosine similarity" },
];

const WINDOWS = [
  { label: "Any time", value: 0 },
  { label: "24h", value: 24 },
  { label: "7d", value: 168 },
  { label: "30d", value: 720 },
];

export function SearchPage() {
  const [q, setQ] = React.useState("");
  const [mode, setMode] = React.useState<SearchMode>("hybrid");
  const [windowHours, setWindowHours] = React.useState(0);

  const search = useMutation({
    mutationFn: () =>
      api.search({ q: q.trim(), mode, limit: 30, window: windowHours || null }),
  });

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (q.trim()) search.mutate();
  };

  const modeHint = MODES.find((m) => m.value === mode)?.hint;

  return (
    <div className="space-y-5">
      <Card>
        <CardContent className="space-y-4 pt-5">
          <form onSubmit={onSubmit} className="flex gap-2">
            <div className="relative flex-1">
              <SearchIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Search the world's news — entities, topics, products…"
                className="h-11 pl-9 text-base"
                autoFocus
              />
            </div>
            <Button type="submit" size="lg" disabled={!q.trim() || search.isPending}>
              {search.isPending ? "Searching…" : "Search"}
            </Button>
          </form>

          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <Tabs value={mode} onValueChange={(v) => setMode(v as SearchMode)}>
                <TabsList>
                  {MODES.map((m) => (
                    <TabsTrigger key={m.value} value={m.value} className="gap-1.5">
                      <m.icon className="h-3.5 w-3.5" />
                      {m.label}
                    </TabsTrigger>
                  ))}
                </TabsList>
              </Tabs>
              <span className="hidden text-xs text-muted-foreground sm:inline">{modeHint}</span>
            </div>
            <div className="flex items-center gap-1.5">
              {WINDOWS.map((w) => (
                <Button
                  key={w.value}
                  type="button"
                  variant={windowHours === w.value ? "secondary" : "ghost"}
                  size="sm"
                  onClick={() => setWindowHours(w.value)}
                >
                  {w.label}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-5">
          {search.isPending ? (
            <ListSkeleton rows={6} />
          ) : search.isError ? (
            <ErrorState message="Search failed." onRetry={() => search.mutate()} />
          ) : !search.data ? (
            <EmptyState
              icon={SearchIcon}
              title="Search across every source and language"
              description="Pick a mode and enter a query. Hybrid fuses keyword and semantic relevance."
            />
          ) : (
            <>
              <div className="mb-3 flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  {search.data.length} result{search.data.length === 1 ? "" : "s"}
                </p>
                <Badge variant="outline" className="capitalize">
                  {mode}
                </Badge>
              </div>
              <ArticleList articles={search.data} showScore />
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
