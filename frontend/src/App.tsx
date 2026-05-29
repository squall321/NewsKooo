import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "@/components/AppShell";
import { DashboardPage } from "@/pages/Dashboard";
import { SearchPage } from "@/pages/Search";
import { TrendsPage } from "@/pages/Trends";
import { IssuesPage } from "@/pages/Issues";
import { ReportsPage } from "@/pages/Reports";
import { SourcesPage } from "@/pages/Sources";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<DashboardPage />} />
        <Route path="search" element={<SearchPage />} />
        <Route path="trends" element={<TrendsPage />} />
        <Route path="issues" element={<IssuesPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="sources" element={<SourcesPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
