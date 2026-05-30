import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  type SortingState,
  useReactTable,
} from "@tanstack/react-table";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  ArrowUpDown,
  FileText,
  LineChart as LineChartIcon,
  Minus,
  Newspaper,
  Search,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState, ListSkeleton } from "@/components/states";
import type { Security, Signal, SignalDirection } from "@/lib/types";
import { cn, formatAxisTime, formatDateTime, formatPct, formatSigned } from "@/lib/utils";

// ── Direction styling ─────────────────────────────────────────────────────────
const directionMeta: Record<
  SignalDirection,
  { label: string; text: string; chip: "success" | "destructive" | "muted"; bar: string; icon: typeof TrendingUp }
> = {
  bullish: { label: "Bullish", text: "text-success", chip: "success", bar: "bg-success", icon: TrendingUp },
  bearish: { label: "Bearish", text: "text-destructive", chip: "destructive", bar: "bg-destructive", icon: TrendingDown },
  neutral: { label: "Neutral", text: "text-muted-foreground", chip: "muted", bar: "bg-muted-foreground", icon: Minus },
};

function DirectionBadge({ direction }: { direction: SignalDirection }) {
  const meta = directionMeta[direction];
  const Icon = meta.icon;
  return (
    <Badge variant={meta.chip} className="gap-1">
      <Icon className="h-3 w-3" />
      {meta.label}
    </Badge>
  );
}

/** Horizontal magnitude bar, tinted by direction. */
function MagnitudeBar({ magnitude, direction }: { magnitude: number; direction: SignalDirection }) {
  const meta = directionMeta[direction];
  const pct = Math.round(Math.max(0, Math.min(1, magnitude)) * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <div className={cn("h-full rounded-full transition-all", meta.bar)} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-9 shrink-0 text-right text-xs tabular-nums text-muted-foreground">{pct}%</span>
    </div>
  );
}

// ── Top signals ────────────────────────────────────────────────────────────────
function TopSignalCard({
  signal,
  security,
  active,
  onSelect,
}: {
  signal: Signal;
  security?: Security;
  active: boolean;
  onSelect: () => void;
}) {
  const meta = directionMeta[signal.direction];
  const provenance = signal.supporting_article_ids.length + signal.supporting_event_ids.length;
  return (
    <button
      onClick={onSelect}
      className={cn(
        "w-full rounded-lg border p-3 text-left transition-colors",
        active ? "border-primary/50 bg-primary/10" : "border-border/60 hover:bg-accent",
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold">{security?.symbol ?? `#${signal.security_id}`}</p>
          <p className="truncate text-xs text-muted-foreground">{security?.name ?? "Unknown security"}</p>
        </div>
        <div className="shrink-0 text-right">
          <span className={cn("block text-base font-semibold tabular-nums", meta.text)}>
            {formatSigned(signal.score)}
          </span>
          <DirectionBadge direction={signal.direction} />
        </div>
      </div>
      <div className="mt-2.5">
        <MagnitudeBar magnitude={signal.magnitude} direction={signal.direction} />
      </div>
      <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
        <span>conf {formatPct(signal.confidence)}</span>
        <span>{signal.horizon_hours}h horizon</span>
        <span className="inline-flex items-center gap-1">
          <FileText className="h-3 w-3" /> {provenance}
        </span>
      </div>
    </button>
  );
}

// ── Signal history mini-chart ───────────────────────────────────────────────────
interface HistoryPoint {
  as_of: string;
  score: number;
  confidence: number;
  magnitude: number;
}

interface TipPayload {
  payload: HistoryPoint;
}

function HistoryTooltip({ active, payload }: { active?: boolean; payload?: TipPayload[] }) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return (
    <div className="rounded-lg border border-border bg-card/95 px-3 py-2 text-xs shadow-lg backdrop-blur">
      <p className="mb-1 font-medium text-foreground">{formatDateTime(p.as_of)}</p>
      <p className="text-muted-foreground">
        Score <span className="font-medium text-foreground">{formatSigned(p.score)}</span>
      </p>
      <p className="text-muted-foreground">
        Magnitude <span className="font-medium text-foreground">{formatPct(p.magnitude)}</span>
      </p>
      <p className="text-muted-foreground">
        Confidence <span className="font-medium text-foreground">{formatPct(p.confidence)}</span>
      </p>
    </div>
  );
}

function SignalHistoryChart({ signals }: { signals: Signal[] }) {
  // API returns newest-first; chart wants chronological order.
  const points: HistoryPoint[] = React.useMemo(
    () =>
      signals
        .slice()
        .reverse()
        .map((s) => ({
          as_of: s.as_of,
          score: s.score,
          confidence: s.confidence,
          magnitude: s.magnitude,
        })),
    [signals],
  );

  const axisProps = {
    stroke: "hsl(var(--muted-foreground))",
    fontSize: 11,
    tickLine: false,
    axisLine: false,
  };

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={points} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
        <defs>
          <linearGradient id="signalScore" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="hsl(var(--success))" />
            <stop offset="50%" stopColor="hsl(var(--muted-foreground))" />
            <stop offset="100%" stopColor="hsl(var(--destructive))" />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
        <XAxis dataKey="as_of" tickFormatter={formatAxisTime} minTickGap={40} {...axisProps} />
        <YAxis domain={[-1, 1]} width={40} ticks={[-1, -0.5, 0, 0.5, 1]} {...axisProps} />
        <Tooltip content={<HistoryTooltip />} />
        <ReferenceLine y={0} stroke="hsl(var(--border))" />
        <Line type="monotone" dataKey="score" stroke="url(#signalScore)" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

// ── Per-security detail panel ────────────────────────────────────────────────────
function SecurityDetail({ security }: { security: Security }) {
  const history = useQuery({
    queryKey: ["signals", "history", security.id],
    queryFn: () => api.getSignals({ security_id: security.id, limit: 60 }),
  });

  const latest = history.data?.items[0];
  const totalArticles = React.useMemo(
    () => new Set((history.data?.items ?? []).flatMap((s) => s.supporting_article_ids)).size,
    [history.data],
  );
  const totalEvents = React.useMemo(
    () => new Set((history.data?.items ?? []).flatMap((s) => s.supporting_event_ids)).size,
    [history.data],
  );

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="min-w-0">
            <CardTitle className="flex items-center gap-2 text-base">
              <span className="font-mono">{security.symbol}</span>
              {latest && <DirectionBadge direction={latest.direction} />}
            </CardTitle>
            <p className="mt-1 truncate text-sm text-muted-foreground">{security.name}</p>
          </div>
          <div className="flex flex-wrap gap-1.5">
            <Badge variant="secondary" className="uppercase">
              {security.asset_class}
            </Badge>
            {security.exchange && <Badge variant="outline">{security.exchange}</Badge>}
            {security.country && security.country !== "—" && (
              <Badge variant="muted">{security.country}</Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {history.isLoading ? (
          <ListSkeleton rows={5} />
        ) : history.isError ? (
          <ErrorState onRetry={() => history.refetch()} />
        ) : !history.data?.items.length ? (
          <EmptyState
            icon={LineChartIcon}
            title="No signals yet"
            description="No model output has been produced for this security in the available window."
          />
        ) : (
          <div className="space-y-4">
            {/* Latest signal summary */}
            {latest && (
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <div className="rounded-lg border border-border/60 p-3">
                  <p className="text-xs text-muted-foreground">Latest score</p>
                  <p className={cn("text-lg font-semibold tabular-nums", directionMeta[latest.direction].text)}>
                    {formatSigned(latest.score)}
                  </p>
                </div>
                <div className="rounded-lg border border-border/60 p-3">
                  <p className="text-xs text-muted-foreground">Magnitude</p>
                  <p className="text-lg font-semibold tabular-nums">{formatPct(latest.magnitude)}</p>
                </div>
                <div className="rounded-lg border border-border/60 p-3">
                  <p className="text-xs text-muted-foreground">Confidence</p>
                  <p className="text-lg font-semibold tabular-nums">{formatPct(latest.confidence)}</p>
                </div>
                <div className="rounded-lg border border-border/60 p-3">
                  <p className="text-xs text-muted-foreground">As of</p>
                  <p className="text-sm font-medium">{formatDateTime(latest.as_of)}</p>
                </div>
              </div>
            )}

            {/* History chart */}
            <div>
              <p className="mb-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Score history (-1 to +1)
              </p>
              <SignalHistoryChart signals={history.data.items} />
            </div>

            {/* Provenance */}
            <div className="flex flex-wrap items-center gap-2 border-t border-border pt-3 text-sm">
              <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Provenance
              </span>
              <Badge variant="secondary" className="gap-1">
                <Newspaper className="h-3 w-3" /> {totalArticles} articles
              </Badge>
              <Badge variant="secondary" className="gap-1">
                <FileText className="h-3 w-3" /> {totalEvents} events
              </Badge>
              <span className="text-xs text-muted-foreground">
                across {history.data.items.length} signals
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Securities table ────────────────────────────────────────────────────────────
function SecuritiesTable({
  securities,
  loading,
  selectedId,
  onSelect,
}: {
  securities: Security[];
  loading: boolean;
  selectedId: number | null;
  onSelect: (s: Security) => void;
}) {
  const [sorting, setSorting] = React.useState<SortingState>([]);

  const columns = React.useMemo<ColumnDef<Security>[]>(
    () => [
      {
        accessorKey: "symbol",
        header: ({ column }) => (
          <button
            className="inline-flex items-center gap-1 hover:text-foreground"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          >
            Symbol <ArrowUpDown className="h-3 w-3" />
          </button>
        ),
        cell: ({ row }) => (
          <div className="min-w-0">
            <span className="font-mono font-medium">{row.original.symbol}</span>
            <p className="truncate text-xs text-muted-foreground">{row.original.name}</p>
          </div>
        ),
      },
      {
        accessorKey: "asset_class",
        header: "Class",
        cell: ({ getValue }) => (
          <Badge variant="secondary" className="uppercase">
            {getValue<string>()}
          </Badge>
        ),
      },
      {
        accessorKey: "exchange",
        header: "Exchange",
        cell: ({ getValue }) => <span className="text-sm">{getValue<string | null>() ?? "—"}</span>,
      },
      {
        accessorKey: "country",
        header: "Country",
        cell: ({ getValue }) => (
          <span className="text-sm text-muted-foreground">{getValue<string | null>() ?? "—"}</span>
        ),
      },
    ],
    [],
  );

  const table = useReactTable({
    data: securities,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <Table>
      <TableHeader>
        {table.getHeaderGroups().map((hg) => (
          <TableRow key={hg.id}>
            {hg.headers.map((header) => (
              <TableHead key={header.id}>
                {header.isPlaceholder
                  ? null
                  : flexRender(header.column.columnDef.header, header.getContext())}
              </TableHead>
            ))}
          </TableRow>
        ))}
      </TableHeader>
      <TableBody>
        {loading ? (
          Array.from({ length: 8 }).map((_, i) => (
            <TableRow key={i}>
              {columns.map((_c, j) => (
                <TableCell key={j}>
                  <Skeleton className="h-5 w-full" />
                </TableCell>
              ))}
            </TableRow>
          ))
        ) : table.getRowModel().rows.length ? (
          table.getRowModel().rows.map((row) => (
            <TableRow
              key={row.id}
              onClick={() => onSelect(row.original)}
              data-state={row.original.id === selectedId ? "selected" : undefined}
              className="cursor-pointer"
            >
              {row.getVisibleCells().map((cell) => (
                <TableCell key={cell.id}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </TableCell>
              ))}
            </TableRow>
          ))
        ) : (
          <TableRow>
            <TableCell colSpan={columns.length} className="py-10 text-center text-muted-foreground">
              No securities match your search.
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export function SignalsPage() {
  const [text, setText] = React.useState("");
  const [assetClass, setAssetClass] = React.useState("");
  const [selectedId, setSelectedId] = React.useState<number | null>(null);

  const securities = useQuery({
    queryKey: ["securities", text, assetClass],
    queryFn: () =>
      api.getSecurities({ q: text || undefined, asset_class: assetClass || undefined, limit: 200 }),
  });

  const top = useQuery({
    queryKey: ["signals", "top"],
    queryFn: () => api.getTopSignals({ window_hours: 24, limit: 8 }),
  });

  const items = React.useMemo(() => securities.data?.items ?? [], [securities.data]);

  const assetClasses = React.useMemo(
    () => Array.from(new Set(items.map((s) => s.asset_class))).sort(),
    [items],
  );

  const secById = React.useMemo(() => new Map(items.map((s) => [s.id, s])), [items]);

  // Default selection: first security once loaded.
  React.useEffect(() => {
    if (selectedId == null && items.length) setSelectedId(items[0].id);
  }, [items, selectedId]);

  const selected = selectedId != null ? secById.get(selectedId) ?? null : null;

  return (
    <div className="space-y-5">
      {/* Top signals */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <LineChartIcon className="h-4 w-4 text-primary" /> Top signals
            <Badge variant="muted" className="ml-1">last 24h</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {top.isLoading ? (
            <ListSkeleton rows={4} />
          ) : top.isError ? (
            <ErrorState onRetry={() => top.refetch()} />
          ) : !top.data?.length ? (
            <EmptyState
              icon={LineChartIcon}
              title="No strong signals"
              description="Nothing crossed the magnitude threshold in this window."
            />
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {top.data.map((sig) => (
                <TopSignalCard
                  key={sig.id}
                  signal={sig}
                  security={secById.get(sig.security_id)}
                  active={sig.security_id === selectedId}
                  onSelect={() => setSelectedId(sig.security_id)}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-[22rem_1fr]">
        {/* Securities list */}
        <Card className="flex flex-col">
          <CardHeader className="gap-3 pb-3">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Search securities…"
                className="pl-9"
              />
            </div>
            <div className="flex flex-wrap gap-1.5">
              <Button
                size="sm"
                variant={assetClass === "" ? "secondary" : "ghost"}
                onClick={() => setAssetClass("")}
              >
                All
              </Button>
              {assetClasses.map((ac) => (
                <Button
                  key={ac}
                  size="sm"
                  variant={assetClass === ac ? "secondary" : "ghost"}
                  onClick={() => setAssetClass(ac)}
                  className="uppercase"
                >
                  {ac}
                </Button>
              ))}
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            {securities.isError ? (
              <ErrorState onRetry={() => securities.refetch()} />
            ) : (
              <>
                <div className="mb-2 text-xs text-muted-foreground">
                  {securities.isLoading
                    ? "Loading…"
                    : `${items.length} of ${securities.data?.total ?? 0} securities`}
                </div>
                <SecuritiesTable
                  securities={items}
                  loading={securities.isLoading}
                  selectedId={selectedId}
                  onSelect={(s) => setSelectedId(s.id)}
                />
              </>
            )}
          </CardContent>
        </Card>

        {/* Detail */}
        {selected ? (
          <SecurityDetail security={selected} />
        ) : (
          <Card>
            <CardContent className="pt-5">
              <EmptyState
                icon={LineChartIcon}
                title="Select a security"
                description="Pick a security to see its signal history and provenance."
              />
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
