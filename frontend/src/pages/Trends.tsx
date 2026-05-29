import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity, Gauge, Sigma, TrendingUp } from "lucide-react";
import { api } from "@/lib/api";
import { TrendChart } from "@/components/TrendChart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ErrorState, ListSkeleton } from "@/components/states";
import type { TargetType, TrendSeries } from "@/lib/types";
import { cn, formatSigned } from "@/lib/utils";

const TYPES: { value: TargetType; label: string }[] = [
  { value: "topic", label: "Topics" },
  { value: "entity", label: "Entities" },
  { value: "keyword", label: "Keywords" },
];

const WINDOWS = [
  { label: "24h", value: 24 },
  { label: "7d", value: 168 },
  { label: "30d", value: 720 },
];

function MoversList({
  series,
  selectedId,
  onSelect,
}: {
  series: TrendSeries[];
  selectedId: number | null;
  onSelect: (s: TrendSeries) => void;
}) {
  return (
    <ul className="space-y-1.5">
      {series.map((t) => {
        const latest = t.points.at(-1);
        const z = latest?.zscore ?? 0;
        const active = t.target_id === selectedId;
        return (
          <li key={`${t.target_type}:${t.target_id}`}>
            <button
              onClick={() => onSelect(t)}
              className={cn(
                "flex w-full items-center justify-between gap-2 rounded-lg border px-3 py-2 text-left transition-colors",
                active ? "border-primary/50 bg-primary/10" : "border-border/60 hover:bg-accent",
              )}
            >
              <span className="min-w-0">
                <span className="block truncate text-sm font-medium">{t.label}</span>
                <span className="text-xs capitalize text-muted-foreground">{t.target_type}</span>
              </span>
              <Badge variant={z >= 3 ? "warning" : "muted"} className="shrink-0 tabular-nums">
                z {formatSigned(z)}
              </Badge>
            </button>
          </li>
        );
      })}
    </ul>
  );
}

export function TrendsPage() {
  const [type, setType] = React.useState<TargetType>("topic");
  const [windowHours, setWindowHours] = React.useState(168);
  const [selected, setSelected] = React.useState<{ id: number; type: TargetType } | null>(null);

  const movers = useQuery({
    queryKey: ["trends", "top", type, windowHours],
    queryFn: () => api.topTrends({ metric: "zscore", target_type: type, window: windowHours, limit: 12 }),
  });

  // Default selection = first mover for the current type.
  React.useEffect(() => {
    const first = movers.data?.[0];
    if (first && (!selected || selected.type !== type)) {
      setSelected({ id: first.target_id, type: first.target_type as TargetType });
    }
  }, [movers.data, type, selected]);

  const series = useQuery({
    queryKey: ["trend", selected?.type, selected?.id, windowHours],
    queryFn: () => api.getTrend({ target_type: selected!.type, target_id: selected!.id, window: windowHours }),
    enabled: !!selected,
  });

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Tabs value={type} onValueChange={(v) => setType(v as TargetType)}>
          <TabsList>
            {TYPES.map((t) => (
              <TabsTrigger key={t.value} value={t.value}>
                {t.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
        <div className="flex items-center gap-1.5">
          {WINDOWS.map((w) => (
            <Button
              key={w.value}
              variant={windowHours === w.value ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setWindowHours(w.value)}
            >
              {w.label}
            </Button>
          ))}
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        {/* Movers list */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-warning" /> Top movers
            </CardTitle>
          </CardHeader>
          <CardContent>
            {movers.isLoading ? (
              <ListSkeleton rows={6} />
            ) : movers.isError ? (
              <ErrorState onRetry={() => movers.refetch()} />
            ) : (
              <MoversList
                series={movers.data ?? []}
                selectedId={selected?.id ?? null}
                onSelect={(s) => setSelected({ id: s.target_id, type: s.target_type as TargetType })}
              />
            )}
          </CardContent>
        </Card>

        {/* Charts */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">{series.data?.label ?? "Select a target"}</CardTitle>
          </CardHeader>
          <CardContent>
            {!selected || series.isLoading ? (
              <ListSkeleton rows={5} />
            ) : series.isError ? (
              <ErrorState onRetry={() => series.refetch()} />
            ) : (
              <Tabs defaultValue="count">
                <TabsList>
                  <TabsTrigger value="count" className="gap-1.5">
                    <Activity className="h-3.5 w-3.5" /> Volume
                  </TabsTrigger>
                  <TabsTrigger value="velocity" className="gap-1.5">
                    <Gauge className="h-3.5 w-3.5" /> Velocity
                  </TabsTrigger>
                  <TabsTrigger value="zscore" className="gap-1.5">
                    <Sigma className="h-3.5 w-3.5" /> Z-score
                  </TabsTrigger>
                </TabsList>
                <TabsContent value="count">
                  <TrendChart points={series.data!.points} metric="count" height={300} />
                </TabsContent>
                <TabsContent value="velocity">
                  <TrendChart points={series.data!.points} metric="velocity" height={300} />
                </TabsContent>
                <TabsContent value="zscore">
                  <TrendChart points={series.data!.points} metric="zscore" height={300} />
                </TabsContent>
              </Tabs>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
