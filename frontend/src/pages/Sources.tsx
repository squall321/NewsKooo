import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  type SortingState,
  useReactTable,
} from "@tanstack/react-table";
import { ArrowUpDown, Globe, Power, PowerOff, Search } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
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
import { toast } from "@/components/ui/sonner";
import { ErrorState } from "@/components/states";
import { Skeleton } from "@/components/ui/skeleton";
import type { Source } from "@/lib/types";
import { timeAgo } from "@/lib/utils";

const METHOD_VARIANT: Record<string, "default" | "secondary" | "warning"> = {
  rss: "default",
  api: "secondary",
  html: "warning",
};

export function SourcesPage() {
  const qc = useQueryClient();
  const [region, setRegion] = React.useState("");
  const [category, setCategory] = React.useState("");
  const [enabledFilter, setEnabledFilter] = React.useState<"all" | "enabled" | "disabled">("all");
  const [text, setText] = React.useState("");
  const [sorting, setSorting] = React.useState<SortingState>([]);

  const query = useQuery({
    queryKey: ["sources", region, category, enabledFilter],
    queryFn: () =>
      api.listSources({
        limit: 200,
        region: region || undefined,
        category: category || undefined,
        enabled: enabledFilter === "all" ? undefined : enabledFilter === "enabled",
      }),
  });

  const toggle = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) =>
      enabled ? api.disableSource(id) : api.enableSource(id),
    onSuccess: (src) => {
      toast.success(`Source ${src.enabled ? "enabled" : "disabled"}`, { description: src.name });
      qc.invalidateQueries({ queryKey: ["sources"] });
    },
    onError: (err) => {
      const msg =
        err instanceof ApiError && err.status === 401
          ? "Not authorized — mutations require an API key."
          : "Failed to update source.";
      toast.error(msg);
    },
  });

  const allItems = React.useMemo(() => query.data?.items ?? [], [query.data]);

  // Derive filter option lists from the data.
  const regions = React.useMemo(
    () => Array.from(new Set(allItems.map((s) => s.region).filter(Boolean))) as string[],
    [allItems],
  );
  const categories = React.useMemo(
    () => Array.from(new Set(allItems.flatMap((s) => s.categories))).sort(),
    [allItems],
  );

  const filtered = React.useMemo(
    () =>
      allItems.filter((s) =>
        text ? s.name.toLowerCase().includes(text.toLowerCase()) : true,
      ),
    [allItems, text],
  );

  const columns = React.useMemo<ColumnDef<Source>[]>(
    () => [
      {
        accessorKey: "name",
        header: ({ column }) => (
          <button
            className="inline-flex items-center gap-1 hover:text-foreground"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          >
            Name <ArrowUpDown className="h-3 w-3" />
          </button>
        ),
        cell: ({ row }) => (
          <div className="min-w-0">
            <a
              href={row.original.homepage_url}
              target="_blank"
              rel="noreferrer"
              className="font-medium hover:text-primary"
            >
              {row.original.name}
            </a>
            <p className="truncate text-xs text-muted-foreground">{row.original.homepage_url}</p>
          </div>
        ),
      },
      {
        accessorKey: "fetch_method",
        header: "Method",
        cell: ({ getValue }) => {
          const m = getValue<string>();
          return (
            <Badge variant={METHOD_VARIANT[m] ?? "muted"} className="uppercase">
              {m}
            </Badge>
          );
        },
      },
      {
        accessorKey: "region",
        header: "Region",
        cell: ({ getValue }) => {
          const r = getValue<string | null>();
          return r ? (
            <span className="inline-flex items-center gap-1 text-sm">
              <Globe className="h-3 w-3 text-muted-foreground" />
              {r}
            </span>
          ) : (
            <span className="text-muted-foreground">—</span>
          );
        },
      },
      {
        id: "categories",
        header: "Categories",
        cell: ({ row }) => (
          <div className="flex flex-wrap gap-1">
            {row.original.categories.slice(0, 3).map((c) => (
              <Badge key={c} variant="secondary" className="text-[10px]">
                {c}
              </Badge>
            ))}
            {row.original.categories.length > 3 && (
              <span className="text-xs text-muted-foreground">+{row.original.categories.length - 3}</span>
            )}
          </div>
        ),
      },
      {
        id: "health",
        header: "Last fetch",
        cell: ({ row }) => {
          const h = row.original.health;
          const status = (h?.last_status as string) ?? null;
          return (
            <div className="text-xs">
              <span className="text-muted-foreground">{timeAgo(h?.last_fetch_at as string | undefined)}</span>
              {status && (
                <Badge
                  variant={status === "ok" ? "success" : "destructive"}
                  className="ml-2 text-[10px]"
                >
                  {status}
                </Badge>
              )}
            </div>
          );
        },
      },
      {
        accessorKey: "enabled",
        header: "Status",
        cell: ({ row }) => (
          <Badge variant={row.original.enabled ? "success" : "muted"}>
            {row.original.enabled ? "enabled" : "disabled"}
          </Badge>
        ),
      },
      {
        id: "actions",
        header: "",
        cell: ({ row }) => (
          <Button
            variant={row.original.enabled ? "ghost" : "secondary"}
            size="sm"
            disabled={toggle.isPending}
            onClick={() => toggle.mutate({ id: row.original.id, enabled: row.original.enabled })}
          >
            {row.original.enabled ? (
              <>
                <PowerOff className="h-3.5 w-3.5" /> Disable
              </>
            ) : (
              <>
                <Power className="h-3.5 w-3.5" /> Enable
              </>
            )}
          </Button>
        ),
      },
    ],
    [toggle],
  );

  const table = useReactTable({
    data: filtered,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <div className="space-y-4">
      {/* Filters */}
      <Card>
        <CardContent className="flex flex-wrap items-center gap-3 pt-5">
          <div className="relative min-w-[220px] flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Filter by name…"
              className="pl-9"
            />
          </div>
          <select
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            className="h-9 rounded-md border border-input bg-background/60 px-3 text-sm"
          >
            <option value="">All regions</option>
            {regions.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="h-9 rounded-md border border-input bg-background/60 px-3 text-sm"
          >
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <div className="flex gap-1.5">
            {(["all", "enabled", "disabled"] as const).map((v) => (
              <Button
                key={v}
                size="sm"
                variant={enabledFilter === v ? "secondary" : "ghost"}
                onClick={() => setEnabledFilter(v)}
                className="capitalize"
              >
                {v}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardContent className="pt-5">
          {query.isError ? (
            <ErrorState onRetry={() => query.refetch()} />
          ) : (
            <>
              <div className="mb-2 text-sm text-muted-foreground">
                {query.isLoading ? "Loading…" : `${filtered.length} of ${query.data?.total ?? 0} sources`}
              </div>
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
                  {query.isLoading ? (
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
                      <TableRow key={row.id}>
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
                        No sources match the current filters.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
