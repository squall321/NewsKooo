import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge conditional Tailwind class names, resolving conflicts deterministically. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Compact number formatting (1.2k, 3.4M …). */
const compact = new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 });
export function formatCompact(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "—";
  return compact.format(n);
}

/** Plain grouped integer (1,234). */
const grouped = new Intl.NumberFormat("en");
export function formatInt(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "—";
  return grouped.format(Math.round(n));
}

/** Signed fixed-point (+1.23 / -0.40) for velocity / z-score. */
export function formatSigned(n: number | null | undefined, digits = 2): string {
  if (n == null || Number.isNaN(n)) return "—";
  const s = n.toFixed(digits);
  return n > 0 ? `+${s}` : s;
}

/** A 0..1 ratio as a whole-number percent ("73%"). */
export function formatPct(n: number | null | undefined, digits = 0): string {
  if (n == null || Number.isNaN(n)) return "—";
  return `${(n * 100).toFixed(digits)}%`;
}

/** Short relative time ("3m", "2h", "5d ago") from an ISO string or Date. */
export function timeAgo(input: string | Date | null | undefined): string {
  if (!input) return "—";
  const then = typeof input === "string" ? new Date(input) : input;
  const ms = Date.now() - then.getTime();
  if (Number.isNaN(ms)) return "—";
  const sec = Math.round(ms / 1000);
  if (sec < 60) return `${Math.max(sec, 0)}s ago`;
  const min = Math.round(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.round(min / 60);
  if (hr < 24) return `${hr}h ago`;
  const day = Math.round(hr / 24);
  if (day < 30) return `${day}d ago`;
  const mo = Math.round(day / 30);
  if (mo < 12) return `${mo}mo ago`;
  return `${Math.round(mo / 12)}y ago`;
}

/** Absolute datetime for tooltips / detail. */
export function formatDateTime(input: string | Date | null | undefined): string {
  if (!input) return "—";
  const d = typeof input === "string" ? new Date(input) : input;
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Short time-of-day for chart axes. */
export function formatAxisTime(input: string): string {
  const d = new Date(input);
  if (Number.isNaN(d.getTime())) return input;
  return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit" });
}

/** Stable-ish pseudo-random in [0,1) from a seed — used for deterministic mocks. */
export function seededRandom(seed: number): () => number {
  let s = seed % 2147483647;
  if (s <= 0) s += 2147483646;
  return () => {
    s = (s * 16807) % 2147483647;
    return (s - 1) / 2147483646;
  };
}
