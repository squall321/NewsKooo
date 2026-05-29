import { type LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn, formatCompact } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: number | string | null | undefined;
  icon: LucideIcon;
  hint?: string;
  loading?: boolean;
  accent?: "primary" | "success" | "warning";
}

const accentMap = {
  primary: "bg-primary/15 text-primary",
  success: "bg-success/15 text-success",
  warning: "bg-warning/15 text-warning",
} as const;

export function StatCard({ label, value, icon: Icon, hint, loading, accent = "primary" }: StatCardProps) {
  const display = typeof value === "number" ? formatCompact(value) : value ?? "—";
  return (
    <Card className="animate-fade-in overflow-hidden">
      <CardContent className="flex items-center gap-4 p-5">
        <div className={cn("flex h-11 w-11 shrink-0 items-center justify-center rounded-xl", accentMap[accent])}>
          <Icon className="h-5 w-5" />
        </div>
        <div className="min-w-0">
          <p className="truncate text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
          {loading ? (
            <Skeleton className="mt-1 h-7 w-20" />
          ) : (
            <p className="text-2xl font-semibold tabular-nums leading-tight">{display}</p>
          )}
          {hint && <p className="truncate text-xs text-muted-foreground">{hint}</p>}
        </div>
      </CardContent>
    </Card>
  );
}
