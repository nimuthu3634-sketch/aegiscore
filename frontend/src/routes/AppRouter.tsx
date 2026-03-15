import { Suspense, lazy } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "@/layouts/AppShell";

const LoginPage = lazy(async () => ({ default: (await import("@/pages/LoginPage")).LoginPage }));
const DashboardPage = lazy(async () => ({
  default: (await import("@/pages/DashboardPage")).DashboardPage,
}));
const AlertsPage = lazy(async () => ({ default: (await import("@/pages/AlertsPage")).AlertsPage }));
const IncidentsPage = lazy(async () => ({
  default: (await import("@/pages/IncidentsPage")).IncidentsPage,
}));
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
    <div className="flex min-h-[40vh] items-center justify-center rounded-[1.75rem] bg-white p-8 text-sm text-brand-black/60 shadow-panel">
      Loading workspace...
    </div>
  );
}

export function AppRouter() {
  return (
    <Suspense fallback={<RouteLoader />}>
      <Routes>
        <Route path="/" element={<Navigate replace to="/login" />} />
        <Route path="/login" element={<LoginPage />} />

        <Route element={<AppShell />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/incidents" element={<IncidentsPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/integrations" element={<IntegrationsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  );
}
