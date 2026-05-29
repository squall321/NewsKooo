import { AlertTriangle, Inbox, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

/** Centered empty placeholder. */
export function EmptyState({
  title = "Nothing here yet",
  description,
  icon: Icon = Inbox,
  className,
}: {
  title?: string;
  description?: string;
  icon?: React.ComponentType<{ className?: string }>;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col items-center justify-center gap-2 py-12 text-center", className)}>
      <div className="rounded-full bg-muted p-3 text-muted-foreground">
        <Icon className="h-6 w-6" />
      </div>
      <p className="font-medium">{title}</p>
      {description && <p className="max-w-sm text-sm text-muted-foreground">{description}</p>}
    </div>
  );
}

/** Inline error with optional retry. */
export function ErrorState({
  message = "Something went wrong.",
  onRetry,
  className,
}: {
  message?: string;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col items-center justify-center gap-3 py-12 text-center", className)}>
      <div className="rounded-full bg-destructive/15 p-3 text-destructive">
        <AlertTriangle className="h-6 w-6" />
      </div>
      <p className="max-w-sm text-sm text-muted-foreground">{message}</p>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          <RefreshCw className="h-4 w-4" /> Retry
        </Button>
      )}
    </div>
  );
}

/** Repeated skeleton rows for list loading states. */
export function ListSkeleton({ rows = 5, className }: { rows?: number; className?: string }) {
  return (
    <div className={cn("space-y-3", className)}>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-3">
          <Skeleton className="h-10 w-10 rounded-lg" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
          </div>
        </div>
      ))}
    </div>
  );
}
