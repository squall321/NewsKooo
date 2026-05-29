import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  Activity,
  BellRing,
  FileText,
  LayoutDashboard,
  Newspaper,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
  TrendingUp,
  WifiOff,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { useUiStore } from "@/store/ui";
import { useApiMode } from "@/hooks/useApiMode";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/search", label: "Search", icon: Search },
  { to: "/trends", label: "Trends", icon: TrendingUp },
  { to: "/issues", label: "Issues", icon: BellRing },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/sources", label: "Sources", icon: Newspaper },
];

const titleByPath: Record<string, string> = {
  "/": "Dashboard",
  "/search": "Search",
  "/trends": "Trends & Velocity",
  "/issues": "Issue Alerts",
  "/reports": "Intelligence Reports",
  "/sources": "Source Registry",
};

function Logo({ collapsed }: { collapsed: boolean }) {
  return (
    <div className="flex items-center gap-2.5 px-1">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
        <Activity className="h-4.5 w-4.5" />
      </div>
      {!collapsed && (
        <div className="leading-none">
          <p className="font-semibold tracking-tight">NewsKoo</p>
          <p className="text-[10px] uppercase tracking-widest text-muted-foreground">Intelligence</p>
        </div>
      )}
    </div>
  );
}

function ApiModeBadge() {
  const { offline, forced } = useApiMode();
  if (!offline && !forced) return null;
  return (
    <Badge variant="warning" className="gap-1.5">
      <WifiOff className="h-3 w-3" />
      {forced ? "Mock data" : "Offline — mock data"}
    </Badge>
  );
}

export function AppShell() {
  const collapsed = useUiStore((s) => s.sidebarCollapsed);
  const toggle = useUiStore((s) => s.toggleSidebar);
  const location = useLocation();
  const title = titleByPath[location.pathname] ?? "NewsKoo";

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside
        className={cn(
          "sticky top-0 hidden h-screen flex-col border-r border-border bg-card/50 backdrop-blur transition-[width] duration-200 md:flex",
          collapsed ? "w-[68px]" : "w-60",
        )}
      >
        <div className="flex h-14 items-center px-3">
          <Logo collapsed={collapsed} />
        </div>
        <nav className="flex-1 space-y-1 px-3 py-2">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary/15 text-primary"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground",
                  collapsed && "justify-center px-0",
                )
              }
              title={collapsed ? item.label : undefined}
            >
              <item.icon className="h-4.5 w-4.5 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-border p-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={toggle}
            className={cn("w-full text-muted-foreground", collapsed && "px-0")}
          >
            {collapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
            {!collapsed && <span>Collapse</span>}
          </Button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-border bg-background/80 px-4 backdrop-blur md:px-6">
          <Button variant="ghost" size="icon" className="md:hidden" onClick={toggle}>
            <PanelLeftOpen className="h-4 w-4" />
          </Button>
          <h1 className="text-lg font-semibold tracking-tight">{title}</h1>
          <div className="ml-auto flex items-center gap-2">
            <ApiModeBadge />
            <ThemeToggle />
          </div>
        </header>
        <main className="flex-1 p-4 md:p-6">
          <div className="mx-auto w-full max-w-7xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
