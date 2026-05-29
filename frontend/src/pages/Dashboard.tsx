import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, Database, Layers, Newspaper, Radio, TrendingUp } from "lucide-react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { StatCard } from "@/components/StatCard";
import { TrendChart } from "@/components/TrendChart";
import { EventCard } from "@/components/EventCard";
import { IssueFeed } from "@/components/IssueFeed";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ErrorState, ListSkeleton } from "@/components/states";
import { useStatsStream } from "@/hooks/useStatsStream";
import { formatSigned } from "@/lib/utils";

function TopMovers() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["trends", "top", "zscore"],
    queryFn: () => api.topTrends({ metric: "zscore", limit: 6 }),
  });

  if (isLoading) return <ListSkeleton rows={5} />;
  if (isError) return <ErrorState onRetry={() => refetch()} />;
  if (!data?.length) return <p className="py-8 text-center text-sm text-muted-foreground">No movers yet.</p>;

  return (
    <ul className="space-y-2">
      {data.map((t) => {
        const latest = t.points.at(-1);
        const z = latest?.zscore ?? 0;
        return (
          <li
            key={`${t.target_type}:${t.target_id}`}
            className="flex items-center justify-between gap-3 rounded-lg border border-border/60 px-3 py-2"
          >
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{t.label}</p>
              <p className="text-xs capitalize text-muted-foreground">{t.target_type}</p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={z >= 3 ? "warning" : "muted"} className="tabular-nums">
                z {formatSigned(z)}
              </Badge>
              <Badge variant="secondary" className="tabular-nums">
                {latest?.count ?? 0}
              </Badge>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

function FeaturedTrend() {
  const { data: top } = useQuery({
    queryKey: ["trends", "top", "featured"],
    queryFn: () => api.topTrends({ metric: "zscore", limit: 1 }),
  });
  const target = top?.[0];
  const { data, isLoading } = useQuery({
    queryKey: ["trend", target?.target_type, target?.target_id],
    queryFn: () =>
      api.getTrend({
        target_type: (target!.target_type as "entity" | "topic" | "keyword") ?? "topic",
        target_id: target!.target_id,
        window: 168,
      }),
    enabled: !!target,
  });

  return (
    <Card className="lg:col-span-2">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-primary" />
            Trending signal
          </CardTitle>
          <p className="mt-1 text-sm text-muted-foreground">{data?.label ?? target?.label ?? "Top accelerating target"}</p>
        </div>
        <Button asChild variant="ghost" size="sm">
          <Link to="/trends">
            Explore <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading || !data ? (
          <ListSkeleton rows={4} />
        ) : (
          <TrendChart points={data.points} metric="count" height={220} />
        )}
      </CardContent>
    </Card>
  );
}

function LatestEvents() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["events", "score", 6],
    queryFn: () => api.listEvents({ order: "score", limit: 6 }),
  });

  if (isLoading) return <ListSkeleton rows={4} />;
  if (isError) return <ErrorState onRetry={() => refetch()} />;

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {(data?.items ?? []).map((e) => (
        <EventCard key={e.id} event={e} />
      ))}
    </div>
  );
}

export function DashboardPage() {
  const { stats } = useStatsStream();

  return (
    <div className="space-y-6">
      {/* KPI row */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Articles" value={stats?.articles} icon={Newspaper} loading={!stats} accent="primary" />
        <StatCard label="Events" value={stats?.events} icon={Layers} loading={!stats} accent="success" />
        <StatCard label="Sources" value={stats?.sources} icon={Database} loading={!stats} accent="primary" />
        <StatCard
          label="Enabled sources"
          value={stats?.enabled_sources}
          icon={Radio}
          loading={!stats}
          hint={stats ? `${stats.sources - stats.enabled_sources} disabled` : undefined}
          accent="warning"
        />
      </div>

      {/* Trend + movers */}
      <div className="grid gap-4 lg:grid-cols-3">
        <FeaturedTrend />
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-warning" />
              Top movers
            </CardTitle>
          </CardHeader>
          <CardContent>
            <TopMovers />
          </CardContent>
        </Card>
      </div>

      {/* Events + live issues */}
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-base font-semibold">Top events</h2>
            <Button asChild variant="ghost" size="sm">
              <Link to="/trends">
                All trends <ArrowUpRight className="h-3.5 w-3.5" />
              </Link>
            </Button>
          </div>
          <LatestEvents />
        </div>
        <Card>
          <CardContent className="pt-5">
            <IssueFeed height={460} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
