"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { AlertTrendChart } from "@/components/charts/alert-trend-chart";
import { ComparisonBarChart } from "@/components/charts/comparison-bar-chart";
import { DonutChart } from "@/components/charts/donut-chart";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, createQueryString } from "@/lib/api";
import { formatDate, formatNumber, scoreTone, truncate } from "@/lib/format";
import { PageHeader } from "@/components/shared/page-header";
import { StatCard } from "@/components/shared/stat-card";
import { useRealtimeStatus } from "@/hooks/use-alert-stream";
import type { Alert, DashboardSummary, Incident, Integration, PageResult } from "@/types/domain";

function buildIncidentStatusData(incidents: Incident[]) {
  const counts = incidents.reduce<Record<string, number>>((accumulator, incident) => {
    accumulator[incident.status] = (accumulator[incident.status] ?? 0) + 1;
    return accumulator;
  }, {});

  return Object.entries(counts).map(([name, value]) => ({ name, value }));
}

function buildUserExposure(alerts: Alert[], incidents: Incident[]) {
  const counts = new Map<string, { label: string; alertCount: number; incidentCount: number }>();

  for (const alert of alerts) {
    if (!alert.assignee) {
      continue;
    }
    const current = counts.get(alert.assignee.id) ?? { label: alert.assignee.full_name, alertCount: 0, incidentCount: 0 };
    current.alertCount += 1;
    counts.set(alert.assignee.id, current);
  }

  for (const incident of incidents) {
    if (!incident.assignee) {
      continue;
    }
    const current = counts.get(incident.assignee.id) ?? { label: incident.assignee.full_name, alertCount: 0, incidentCount: 0 };
    current.incidentCount += 1;
    counts.set(incident.assignee.id, current);
  }

  return [...counts.values()]
    .map((entry) => ({ ...entry, total: entry.alertCount + entry.incidentCount }))
    .sort((left, right) => right.total - left.total)
    .slice(0, 5)
    .map((entry) => ({ label: entry.label, total: entry.total }));
}

function buildSourceComparison(alerts: Alert[]) {
  const groups = alerts.reduce<Record<string, { label: string; count: number }>>((accumulator, alert) => {
    accumulator[alert.source] = accumulator[alert.source] ?? { label: alert.source, count: 0 };
    accumulator[alert.source].count += 1;
    return accumulator;
  }, {});
  return Object.values(groups);
}

export default function DashboardPage() {
  const realtimeStatus = useRealtimeStatus();
  const summaryQuery = useQuery({
    queryKey: ["dashboard", "summary"],
    queryFn: () => api.get<DashboardSummary>("/dashboard/summary"),
  });
  const alertsQuery = useQuery({
    queryKey: ["alerts", "dashboard-open"],
    queryFn: () => api.get<PageResult<Alert>>(`/alerts${createQueryString({ status: "open", page: 1, page_size: 40 })}`),
  });
  const incidentsQuery = useQuery({
    queryKey: ["incidents", "dashboard-open"],
    queryFn: () => api.get<PageResult<Incident>>(`/incidents${createQueryString({ page: 1, page_size: 40 })}`),
  });
  const integrationsQuery = useQuery({
    queryKey: ["integrations", "dashboard"],
    queryFn: () => api.get<PageResult<Integration>>(`/integrations${createQueryString({ page: 1, page_size: 8 })}`),
  });

  if (summaryQuery.isLoading) {
    return <LoadingState lines={5} compact />;
  }

  if (summaryQuery.isError || !summaryQuery.data) {
    return <ErrorState description={summaryQuery.error instanceof Error ? summaryQuery.error.message : "Dashboard data could not be loaded."} onRetry={() => summaryQuery.refetch()} />;
  }

  const summary = summaryQuery.data;
  const alerts = alertsQuery.data?.items ?? [];
  const incidents = incidentsQuery.data?.items ?? [];
  const integrations = integrationsQuery.data?.items ?? [];
  const userExposure = buildUserExposure(alerts, incidents);
  const sourceComparison = buildSourceComparison(alerts);
  const incidentStatus = buildIncidentStatusData(incidents);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Operational overview"
        title="SOC dashboard"
        description="Track live alert pressure, incident progression, integration health, and high-risk assets from one analyst-first control surface."
        actions={<Badge tone={realtimeStatus}>{realtimeStatus === "connected" ? "Live channel active" : `Realtime ${realtimeStatus}`}</Badge>}
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <StatCard label="Open alerts" value={formatNumber(summary.kpis.open_alerts)} detail="Active triage queue" tone={scoreTone(summary.kpis.average_risk_score)} />
        <StatCard label="Open incidents" value={formatNumber(summary.kpis.open_incidents)} detail="Cases requiring workflow attention" />
        <StatCard label="Tracked assets" value={formatNumber(summary.kpis.total_assets)} detail="Endpoints with current visibility" />
        <StatCard label="Ingestion today" value={formatNumber(summary.kpis.ingestion_today)} detail="Imported log volume in current day" />
        <StatCard label="Average risk" value={summary.kpis.average_risk_score.toFixed(1)} detail="Mean open alert priority score" tone={scoreTone(summary.kpis.average_risk_score)} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Alert trend</CardTitle>
          </CardHeader>
          <CardContent>
            <AlertTrendChart data={summary.alert_trend} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Incidents by status</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 lg:grid-cols-[220px_1fr]">
            <DonutChart data={incidentStatus.length ? incidentStatus : [{ name: "open", value: 0 }]} />
            <div className="space-y-3">
              {incidentStatus.length ? (
                incidentStatus.map((item) => (
                  <div key={item.name} className="flex items-center justify-between rounded-2xl border px-4 py-3">
                    <span className="font-medium capitalize">{item.name}</span>
                    <Badge tone={item.name}>{item.value}</Badge>
                  </div>
                ))
              ) : (
                <p className="text-sm text-[#6f6f6f]">No incident status data is available yet.</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <CardHeader>
            <CardTitle>Integration health</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2">
            {integrations.length ? (
              integrations.map((integration) => (
                <div key={integration.id} className="rounded-[1.5rem] border bg-[#fcfcfc] p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-semibold text-[#111111]">{integration.name}</p>
                      <p className="mt-1 text-sm text-[#6f6f6f]">{integration.description}</p>
                    </div>
                    <Badge tone={integration.health_status}>{integration.health_status}</Badge>
                  </div>
                  <p className="mt-4 text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">
                    Last sync {integration.last_synced_at ? formatDate(integration.last_synced_at) : "not yet recorded"}
                  </p>
                </div>
              ))
            ) : (
              <p className="text-sm text-[#6f6f6f]">Integration health will appear here once telemetry sources are active.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent activity</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {summary.recent_activity.map((entry) => (
              <div key={entry.id} className="rounded-[1.5rem] border bg-[#fcfcfc] p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold text-[#111111]">{entry.title}</p>
                    <p className="mt-1 text-sm leading-6 text-[#6f6f6f]">{truncate(entry.summary, 96)}</p>
                  </div>
                  <Badge tone={entry.kind === "incident" ? "high" : "medium"}>{entry.kind}</Badge>
                </div>
                <p className="mt-4 text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">{formatDate(entry.timestamp)}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <CardHeader>
            <CardTitle>Risky assets</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {summary.risky_assets.map((asset) => (
              <Link key={asset.id} href={`/assets/${asset.id}`} className="block rounded-[1.5rem] border bg-[#fcfcfc] p-4 transition hover:border-[#FF7A1A]">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-semibold text-[#111111]">{asset.hostname}</p>
                    <p className="mt-1 text-sm text-[#6f6f6f]">{asset.ip_address ?? "IP unavailable"}</p>
                  </div>
                  <Badge tone={scoreTone(asset.risk_score)}>{asset.risk_score.toFixed(1)}</Badge>
                </div>
                <p className="mt-3 text-sm leading-6 text-[#6f6f6f]">{asset.risk_summary ?? "No current risk summary."}</p>
              </Link>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>User exposure widget</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {userExposure.length ? (
              <>
                <ComparisonBarChart data={userExposure} dataKey="total" />
                <div className="grid gap-3">
                  {userExposure.map((entry) => (
                    <div key={entry.label} className="flex items-center justify-between rounded-2xl border px-4 py-3">
                      <span className="font-medium">{entry.label}</span>
                      <Badge tone={entry.total >= 4 ? "high" : "medium"}>{entry.total} active cases</Badge>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <p className="text-sm text-[#6f6f6f]">User exposure will appear when alerts or incidents are assigned to analysts.</p>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Alert source comparison</CardTitle>
        </CardHeader>
        <CardContent>
          <ComparisonBarChart data={sourceComparison.length ? sourceComparison : [{ label: "No data", count: 0 }]} dataKey="count" />
        </CardContent>
      </Card>
    </div>
  );
}
