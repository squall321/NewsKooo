import { useQuery } from "@tanstack/react-query";
import { BellRing, Clock } from "lucide-react";
import { api } from "@/lib/api";
import { IssueFeed, IssueRow } from "@/components/IssueFeed";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { EmptyState, ErrorState, ListSkeleton } from "@/components/states";

function CurrentIssues() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["issues", "current"],
    queryFn: () => api.listIssues({ window: 24, limit: 50 }),
    refetchInterval: 60_000,
  });

  if (isLoading) return <ListSkeleton rows={6} />;
  if (isError) return <ErrorState onRetry={() => refetch()} />;
  if (!data?.length)
    return (
      <EmptyState
        icon={Clock}
        title="No active issues"
        description="Nothing is currently above the anomaly threshold in this window."
      />
    );

  return (
    <div className="space-y-2">
      {data.map((issue) => (
        <IssueRow key={`${issue.target_type}:${issue.target_id}`} issue={issue} />
      ))}
    </div>
  );
}

export function IssuesPage() {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card className="flex flex-col">
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle className="flex items-center gap-2">
            <BellRing className="h-4 w-4 text-primary" /> Live stream
          </CardTitle>
        </CardHeader>
        <CardContent className="flex-1 pt-0">
          <IssueFeed height={560} showHeader />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-warning" /> Current anomalies
          </CardTitle>
          <Badge variant="muted">last 24h</Badge>
        </CardHeader>
        <CardContent>
          <CurrentIssues />
        </CardContent>
      </Card>
    </div>
  );
}
