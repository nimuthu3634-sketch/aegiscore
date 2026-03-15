import { Suspense, lazy } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "@/layouts/AppShell";
import { ProtectedRoute } from "@/routes/ProtectedRoute";
import { PublicOnlyRoute } from "@/routes/PublicOnlyRoute";

const LoginPage = lazy(async () => ({ default: (await import("@/pages/LoginPage")).LoginPage }));
const DashboardPage = lazy(async () => ({
  default: (await import("@/pages/DashboardPage")).DashboardPage,
}));
const AlertsPage = lazy(async () => ({ default: (await import("@/pages/AlertsPage")).AlertsPage }));
const IncidentsPage = lazy(async () => ({
  default: (await import("@/pages/IncidentsPage")).IncidentsPage,
}));
const LogsPage = lazy(async () => ({ default: (await import("@/pages/LogsPage")).LogsPage }));
const ReportsPage = lazy(async () => ({ default: (await import("@/pages/ReportsPage")).ReportsPage }));
const IntegrationsPage = lazy(async () => ({
  default: (await import("@/pages/IntegrationsPage")).IntegrationsPage,
}));
const SettingsPage = lazy(async () => ({ default: (await import("@/pages/SettingsPage")).SettingsPage }));
const NotFoundPage = lazy(async () => ({
  default: (await import("@/pages/NotFoundPage")).NotFoundPage,
}));

function RouteLoader() {
  return (
    <div className="panel flex min-h-[40vh] flex-col items-center justify-center rounded-[1.9rem] p-8 text-center shadow-premium">
      <div className="flex h-14 w-14 items-center justify-center rounded-[1.2rem] bg-brand-orange/10 text-brand-orange shadow-soft">
        <div className="h-5 w-5 animate-pulse rounded-full bg-brand-orange/80" />
      </div>
      <p className="mt-4 text-sm font-semibold text-brand-black">Loading workspace</p>
      <p className="mt-2 text-sm leading-6 text-brand-black/55">
        Preparing the AegisCore dashboard, alert feeds, and analyst views.
      </p>
    </div>
  );
}

export function AppRouter() {
  return (
    <Suspense fallback={<RouteLoader />}>
      <Routes>
        <Route path="/" element={<Navigate replace to="/dashboard" />} />

        <Route element={<PublicOnlyRoute />}>
          <Route path="/login" element={<LoginPage />} />
        </Route>

        <Route element={<ProtectedRoute />}>
          <Route element={<AppShell />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/alerts" element={<AlertsPage />} />
            <Route path="/incidents" element={<IncidentsPage />} />
            <Route path="/logs" element={<LogsPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/integrations" element={<IntegrationsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  );
}
