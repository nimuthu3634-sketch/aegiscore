"use client";

import { useQuery } from "@tanstack/react-query";

import { AppShell } from "@/components/layout/app-shell";
import { AlertTrendChart } from "@/components/charts/alert-trend-chart";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { DashboardSummary } from "@/types/domain";

export default function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard", "summary"],
    queryFn: () => api.get<DashboardSummary>("/dashboard/summary"),
  });

  return (
    <AppShell title="SOC Overview">
      {isLoading || !data ? (
        <div className="rounded-2xl border bg-white p-10 text-center shadow-panel">Loading dashboard...</div>
      ) : (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
            {[
              ["Open alerts", data.kpis.open_alerts],
              ["Open incidents", data.kpis.open_incidents],
              ["Tracked assets", data.kpis.total_assets],
              ["Ingestion today", data.kpis.ingestion_today],
              ["Average risk", data.kpis.average_risk_score],
            ].map(([label, value]) => (
              <Card key={label}>
                <CardContent className="py-6">
                  <p className="text-sm text-[var(--muted)]">{label}</p>
                  <p className="mt-3 text-3xl font-semibold">{value}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="grid gap-6 xl:grid-cols-[1.5fr_0.9fr]">
            <Card>
              <CardHeader>
                <CardTitle>Alert pressure over the last 7 days</CardTitle>
              </CardHeader>
              <CardContent>
                <AlertTrendChart data={data.alert_trend} />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Integration health</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {Object.entries(data.integration_health).map(([name, health]) => (
                  <div key={name} className="flex items-center justify-between rounded-2xl border px-4 py-3">
                    <div>
                      <p className="font-semibold">{name}</p>
                      <p className="text-sm text-[var(--muted)]">Telemetry source status</p>
                    </div>
                    <Badge tone={health}>{health}</Badge>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Top risky assets</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {data.risky_assets.map((asset) => (
                  <div key={asset.id} className="flex items-center justify-between rounded-2xl border px-4 py-3">
                    <div>
                      <p className="font-semibold">{asset.hostname}</p>
                      <p className="text-sm text-[var(--muted)]">{asset.risk_summary ?? "No current summary"}</p>
                    </div>
                    <Badge tone={asset.risk_score >= 65 ? "high" : asset.risk_score >= 35 ? "medium" : "low"}>
                      {asset.risk_score}
                    </Badge>
                  </div>
                ))}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Recent activity</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {data.recent_activity.map((entry) => (
                  <div key={entry.id} className="rounded-2xl border px-4 py-3">
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-semibold">{entry.title}</p>
                      <Badge tone={entry.kind === "incident" ? "high" : "medium"}>{entry.kind}</Badge>
                    </div>
                    <p className="mt-2 text-sm text-[var(--muted)]">{entry.summary}</p>
                    <p className="mt-2 text-xs uppercase tracking-wide text-[var(--muted)]">{formatDate(entry.timestamp)}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </AppShell>
  );
}
