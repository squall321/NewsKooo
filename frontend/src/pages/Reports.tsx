import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarClock, FileText, Plus, Sparkles, X } from "lucide-react";
import { api } from "@/lib/api";
import { Markdown } from "@/components/Markdown";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "@/components/ui/sonner";
import { EmptyState, ErrorState, ListSkeleton } from "@/components/states";
import { ApiError } from "@/lib/api";
import type { Report } from "@/lib/types";
import { cn, formatDateTime } from "@/lib/utils";

function GenerateForm({ onCreated }: { onCreated: (r: Report) => void }) {
  const qc = useQueryClient();
  const [keywords, setKeywords] = React.useState<string[]>([]);
  const [draft, setDraft] = React.useState("");
  const [sector, setSector] = React.useState("");
  const [region, setRegion] = React.useState("");
  const [windowHours, setWindowHours] = React.useState(168);

  const addKeyword = () => {
    const k = draft.trim();
    if (k && !keywords.includes(k)) setKeywords((p) => [...p, k]);
    setDraft("");
  };

  const generate = useMutation({
    mutationFn: () =>
      api.generateReport({
        keywords,
        sector: sector.trim() || null,
        region: region.trim() || null,
        window: windowHours,
      }),
    onSuccess: (r) => {
      toast.success("Report generated", { description: r.title });
      qc.invalidateQueries({ queryKey: ["reports"] });
      onCreated(r);
    },
    onError: (err) => {
      const msg =
        err instanceof ApiError && err.status === 503
          ? "Report generation isn't available yet (Phase 9)."
          : "Failed to generate report.";
      toast.error(msg);
    },
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Sparkles className="h-4 w-4 text-primary" /> Generate report
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div>
          <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Keywords</label>
          <div className="flex gap-2">
            <Input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addKeyword();
                }
              }}
              placeholder="e.g. semiconductors"
            />
            <Button type="button" variant="secondary" size="icon" onClick={addKeyword}>
              <Plus className="h-4 w-4" />
            </Button>
          </div>
          {keywords.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {keywords.map((k) => (
                <Badge key={k} variant="secondary" className="gap-1">
                  {k}
                  <button onClick={() => setKeywords((p) => p.filter((x) => x !== k))}>
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
          )}
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Sector</label>
            <Input value={sector} onChange={(e) => setSector(e.target.value)} placeholder="technology" />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Region</label>
            <Input value={region} onChange={(e) => setRegion(e.target.value)} placeholder="asia" />
          </div>
        </div>
        <div>
          <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Window</label>
          <div className="flex gap-1.5">
            {[
              { label: "24h", value: 24 },
              { label: "7d", value: 168 },
              { label: "30d", value: 720 },
            ].map((w) => (
              <Button
                key={w.value}
                type="button"
                size="sm"
                variant={windowHours === w.value ? "secondary" : "ghost"}
                onClick={() => setWindowHours(w.value)}
              >
                {w.label}
              </Button>
            ))}
          </div>
        </div>
        <Button
          className="w-full"
          onClick={() => generate.mutate()}
          disabled={generate.isPending || (keywords.length === 0 && !sector && !region)}
        >
          {generate.isPending ? "Generating…" : "Generate"}
        </Button>
      </CardContent>
    </Card>
  );
}

export function ReportsPage() {
  const [selectedId, setSelectedId] = React.useState<number | null>(null);

  const list = useQuery({
    queryKey: ["reports", "list"],
    queryFn: () => api.listReports({ limit: 50 }),
  });

  React.useEffect(() => {
    if (selectedId == null && list.data?.items.length) setSelectedId(list.data.items[0].id);
  }, [list.data, selectedId]);

  const detail = useQuery({
    queryKey: ["report", selectedId],
    queryFn: () => api.getReport(selectedId!),
    enabled: selectedId != null,
  });

  return (
    <div className="grid gap-4 lg:grid-cols-[20rem_1fr]">
      <div className="space-y-4">
        <GenerateForm onCreated={(r) => setSelectedId(r.id)} />
        <Card className="flex flex-col">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <FileText className="h-4 w-4" /> Reports
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            {list.isLoading ? (
              <ListSkeleton rows={5} />
            ) : list.isError ? (
              <ErrorState onRetry={() => list.refetch()} />
            ) : !list.data?.items.length ? (
              <EmptyState title="No reports yet" description="Generate one to get started." />
            ) : (
              <ScrollArea style={{ maxHeight: 360 }} className="pr-2">
                <ul className="space-y-1.5">
                  {list.data.items.map((r) => (
                    <li key={r.id}>
                      <button
                        onClick={() => setSelectedId(r.id)}
                        className={cn(
                          "w-full rounded-lg border px-3 py-2 text-left transition-colors",
                          r.id === selectedId
                            ? "border-primary/50 bg-primary/10"
                            : "border-border/60 hover:bg-accent",
                        )}
                      >
                        <p className="truncate text-sm font-medium">{r.title}</p>
                        <p className="mt-0.5 flex items-center gap-1.5 text-xs text-muted-foreground">
                          {r.scheduled && <CalendarClock className="h-3 w-3" />}
                          {formatDateTime(r.created_at)}
                        </p>
                      </button>
                    </li>
                  ))}
                </ul>
              </ScrollArea>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Viewer */}
      <Card className="min-h-[60vh]">
        <CardContent className="pt-5">
          {selectedId == null ? (
            <EmptyState icon={FileText} title="Select a report" description="Pick a report to read it." />
          ) : detail.isLoading ? (
            <ListSkeleton rows={8} />
          ) : detail.isError ? (
            <ErrorState onRetry={() => detail.refetch()} />
          ) : detail.data ? (
            <article>
              <header className="mb-4 border-b border-border pb-4">
                <h2 className="text-2xl font-semibold tracking-tight">{detail.data.title}</h2>
                <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                  {detail.data.provider && <Badge variant="muted">{detail.data.provider}</Badge>}
                  {detail.data.model && <Badge variant="outline">{detail.data.model}</Badge>}
                  {detail.data.scheduled && (
                    <Badge variant="secondary" className="gap-1">
                      <CalendarClock className="h-3 w-3" /> scheduled
                    </Badge>
                  )}
                  <span>v{detail.data.version}</span>
                  <span>· {formatDateTime(detail.data.created_at)}</span>
                </div>
                {(detail.data.query.keywords ?? []).length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {(detail.data.query.keywords ?? []).map((k) => (
                      <Badge key={k} variant="secondary" className="text-[10px]">
                        {k}
                      </Badge>
                    ))}
                  </div>
                )}
              </header>
              <Markdown>{detail.data.body_md}</Markdown>
            </article>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
