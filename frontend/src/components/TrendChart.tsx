import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TrendPoint } from "@/lib/types";
import { formatAxisTime, formatDateTime, formatSigned } from "@/lib/utils";

type Metric = "count" | "velocity" | "zscore";

interface TrendChartProps {
  points: TrendPoint[];
  metric?: Metric;
  height?: number;
}

const metricMeta: Record<Metric, { label: string; color: string }> = {
  count: { label: "Mentions", color: "hsl(var(--primary))" },
  velocity: { label: "Velocity", color: "hsl(var(--success))" },
  zscore: { label: "Z-score", color: "hsl(var(--warning))" },
};

interface TipPayload {
  payload: TrendPoint;
}

function ChartTooltip({ active, payload }: { active?: boolean; payload?: TipPayload[] }) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return (
    <div className="rounded-lg border border-border bg-card/95 px-3 py-2 text-xs shadow-lg backdrop-blur">
      <p className="mb-1 font-medium text-foreground">{formatDateTime(p.bucket)}</p>
      <p className="text-muted-foreground">
        Mentions <span className="font-medium text-foreground">{p.count}</span>
      </p>
      <p className="text-muted-foreground">
        Velocity <span className="font-medium text-foreground">{formatSigned(p.velocity)}</span>
      </p>
      <p className="text-muted-foreground">
        Z-score <span className="font-medium text-foreground">{formatSigned(p.zscore)}</span>
      </p>
      <p className="text-muted-foreground">
        Sources <span className="font-medium text-foreground">{p.source_count}</span>
      </p>
    </div>
  );
}

export function TrendChart({ points, metric = "count", height = 240 }: TrendChartProps) {
  const meta = metricMeta[metric];
  const axisProps = {
    stroke: "hsl(var(--muted-foreground))",
    fontSize: 11,
    tickLine: false,
    axisLine: false,
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      {metric === "count" ? (
        <AreaChart data={points} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <defs>
            <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={meta.color} stopOpacity={0.35} />
              <stop offset="100%" stopColor={meta.color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
          <XAxis dataKey="bucket" tickFormatter={formatAxisTime} minTickGap={40} {...axisProps} />
          <YAxis allowDecimals={false} width={40} {...axisProps} />
          <Tooltip content={<ChartTooltip />} />
          <Area
            type="monotone"
            dataKey="count"
            stroke={meta.color}
            strokeWidth={2}
            fill="url(#trendFill)"
          />
        </AreaChart>
      ) : metric === "velocity" ? (
        <BarChart data={points} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
          <XAxis dataKey="bucket" tickFormatter={formatAxisTime} minTickGap={40} {...axisProps} />
          <YAxis width={40} {...axisProps} />
          <Tooltip content={<ChartTooltip />} cursor={{ fill: "hsl(var(--muted) / 0.4)" }} />
          <ReferenceLine y={0} stroke="hsl(var(--border))" />
          <Bar dataKey="velocity" radius={[3, 3, 0, 0]}>
            {points.map((p, i) => (
              <Cell
                key={i}
                fill={p.velocity >= 0 ? "hsl(var(--success))" : "hsl(var(--destructive))"}
              />
            ))}
          </Bar>
        </BarChart>
      ) : (
        <LineChart data={points} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
          <XAxis dataKey="bucket" tickFormatter={formatAxisTime} minTickGap={40} {...axisProps} />
          <YAxis width={40} {...axisProps} />
          <Tooltip content={<ChartTooltip />} />
          <ReferenceLine y={3} stroke="hsl(var(--warning))" strokeDasharray="4 4" />
          <Line type="monotone" dataKey="zscore" stroke={meta.color} strokeWidth={2} dot={false} />
        </LineChart>
      )}
    </ResponsiveContainer>
  );
}
