"use client";

import Link from "next/link";
import { Activity, ArrowUpRight, Radar, ShieldAlert, Sparkles, Workflow } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { AlertTrendChart } from "@/components/charts/alert-trend-chart";
import { ComparisonBarChart } from "@/components/charts/comparison-bar-chart";
import { DonutChart } from "@/components/charts/donut-chart";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { StatCard } from "@/components/shared/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useRealtimeStatus } from "@/hooks/use-alert-stream";
import { api, createQueryString } from "@/lib/api";
import { formatDate, formatNumber, scoreTone, toTitleCase, truncate } from "@/lib/format";
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
    accumulator[alert.source] = accumulator[alert.source] ?? { label: toTitleCase(alert.source), count: 0 };
    accumulator[alert.source].count += 1;
    return accumulator;
  }, {});

  return Object.values(groups);
}

function buildSeverityData(summary: DashboardSummary) {
  return Object.entries(summary.severity_breakdown)
    .map(([name, value]) => ({ name: toTitleCase(name), value }))
    .filter((entry) => entry.value > 0);
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
    return (
      <ErrorState
        description={summaryQuery.error instanceof Error ? summaryQuery.error.message : "Dashboard data could not be loaded."}
        onRetry={() => summaryQuery.refetch()}
      />
    );
  }

  const summary = summaryQuery.data;
  const alerts = alertsQuery.data?.items ?? [];
  const incidents = incidentsQuery.data?.items ?? [];
  const integrations = integrationsQuery.data?.items ?? [];
  const severityData = buildSeverityData(summary);
  const incidentStatus = buildIncidentStatusData(incidents);
  const userExposure = buildUserExposure(alerts, incidents);
  const sourceComparison = buildSourceComparison(alerts);
  const healthyIntegrationCount = integrations.filter((integration) => integration.health_status === "healthy").length;
  const highRiskAlerts = alerts.filter((alert) => alert.risk_score >= 65).length;
  const topAlerts = alerts.slice(0, 4);

  return (
    <div className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-[1.45fr_0.9fr]">
        <section className="relative overflow-hidden rounded-[32px] border border-[#27201a] bg-[#111111] p-6 text-white shadow-[0_34px_70px_rgba(17,17,17,0.2)] xl:p-8">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,122,26,0.22),transparent_28%),linear-gradient(135deg,#171311_0%,#111111_52%,#0f0d0c_100%)]" />
          <div className="absolute right-[-48px] top-[84px] h-[220px] w-[220px] rounded-full bg-[rgba(255,122,26,0.12)] blur-3xl" />
          <div className="relative">
            <div className="flex flex-wrap items-center gap-3">
              <span className="inline-flex rounded-full border border-white/10 bg-white/[0.05] px-3 py-1 text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-[#ffbf92]">
                Operational overview
              </span>
              <span className="text-[11px] uppercase tracking-[0.3em] text-white/42">Presentation-ready command deck</span>
            </div>

            <div className="mt-6 max-w-4xl space-y-4">
              <h1 className="text-4xl font-semibold leading-[0.98] tracking-[-0.06em] text-white xl:text-[3.65rem]">
                Stay ahead of noisy telemetry without losing analyst focus.
              </h1>
              <p className="max-w-3xl text-base leading-7 text-white/72">
                AegisCore turns alerts, incidents, assets, and import-only lab telemetry into one calm defensive surface with
                explainable scoring and presentation-friendly workflows.
              </p>
            </div>

            <div className="mt-8 grid gap-3 md:grid-cols-3">
              <div className="rounded-[24px] border border-white/10 bg-white/[0.05] p-4">
                <p className="text-[11px] uppercase tracking-[0.24em] text-white/42">High-risk queue</p>
                <p className="mt-2 text-3xl font-semibold tracking-[-0.05em] text-white">{formatNumber(highRiskAlerts)}</p>
                <p className="mt-2 text-sm text-white/62">Alerts scoring above 65 and needing confident triage.</p>
              </div>
              <div className="rounded-[24px] border border-white/10 bg-white/[0.05] p-4">
                <p className="text-[11px] uppercase tracking-[0.24em] text-white/42">Incident command</p>
                <p className="mt-2 text-3xl font-semibold tracking-[-0.05em] text-white">{formatNumber(summary.kpis.open_incidents)}</p>
                <p className="mt-2 text-sm text-white/62">Live case workload currently moving through analyst workflow.</p>
              </div>
              <div className="rounded-[24px] border border-white/10 bg-white/[0.05] p-4">
                <p className="text-[11px] uppercase tracking-[0.24em] text-white/42">Healthy integrations</p>
                <p className="mt-2 text-3xl font-semibold tracking-[-0.05em] text-white">
                  {healthyIntegrationCount}/{integrations.length || 0}
                </p>
                <p className="mt-2 text-sm text-white/62">Connected or import-ready telemetry sources in the current workspace.</p>
              </div>
            </div>

            <div className="mt-8 flex flex-wrap gap-2">
              {sourceComparison.slice(0, 4).map((source) => (
                <span key={source.label} className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-2 text-sm text-white/70">
                  {source.label} {formatNumber(source.count)}
                </span>
              ))}
            </div>
          </div>
        </section>

        <Card className="bg-[linear-gradient(180deg,rgba(255,255,255,0.94),rgba(251,246,240,0.9))]">
          <CardContent className="space-y-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[11px] uppercase tracking-[0.28em] text-[#8a7d72]">Signal mix</p>
                <h2 className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-[#111111]">Threat composition and command posture</h2>
              </div>
              <Badge tone={realtimeStatus}>{realtimeStatus === "connected" ? "Live feed" : `Realtime ${realtimeStatus}`}</Badge>
            </div>

            <div className="grid items-center gap-4 lg:grid-cols-[190px_1fr]">
              <DonutChart data={severityData.length ? severityData : [{ name: "Open", value: 0 }]} />
              <div className="space-y-3">
                {severityData.length ? (
                  severityData.map((entry) => (
                    <div key={entry.name} className="flex items-center justify-between rounded-[20px] border border-black/8 bg-white/70 px-4 py-3">
                      <span className="font-medium text-[#171513]">{entry.name}</span>
                      <Badge tone={entry.name.toLowerCase()}>{formatNumber(entry.value)}</Badge>
                    </div>
                  ))
                ) : (
                  <p className="text-sm leading-6 text-[#6d635a]">Severity distribution will appear as soon as active alerts are available.</p>
                )}
              </div>
            </div>

            <div className="rounded-[24px] bg-[#111111] p-4 text-white shadow-[0_20px_42px_rgba(17,17,17,0.16)]">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.24em] text-white/42">Average risk</p>
                  <p className="mt-2 text-3xl font-semibold tracking-[-0.05em] text-white">{summary.kpis.average_risk_score.toFixed(1)}</p>
                </div>
                <div>
                  <p className="text-[11px] uppercase tracking-[0.24em] text-white/42">Open assets</p>
                  <p className="mt-2 text-3xl font-semibold tracking-[-0.05em] text-white">{formatNumber(summary.kpis.total_assets)}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <StatCard
          label="Open alerts"
          value={formatNumber(summary.kpis.open_alerts)}
          detail="Active triage queue across all telemetry sources."
          tone={scoreTone(summary.kpis.average_risk_score)}
        />
        <StatCard label="Open incidents" value={formatNumber(summary.kpis.open_incidents)} detail="Cases currently assigned or awaiting analyst action." />
        <StatCard label="Tracked assets" value={formatNumber(summary.kpis.total_assets)} detail="Endpoints and systems with active visibility in the workspace." />
        <StatCard label="Ingestion today" value={formatNumber(summary.kpis.ingestion_today)} detail="Records imported across current defensive connectors and lab files." />
        <StatCard
          label="Average risk"
          value={summary.kpis.average_risk_score.toFixed(1)}
          detail="Mean score for currently open alerts."
          tone={scoreTone(summary.kpis.average_risk_score)}
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.3fr_0.95fr]">
        <Card>
          <CardHeader>
            <div>
              <p className="text-[11px] uppercase tracking-[0.28em] text-[#8a7d72]">Trendline</p>
              <CardTitle className="mt-2">Alert pressure over time</CardTitle>
            </div>
            <Badge tone="medium">Critical vs high volume</Badge>
          </CardHeader>
          <CardContent>
            <AlertTrendChart data={summary.alert_trend} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div>
              <p className="text-[11px] uppercase tracking-[0.28em] text-[#8a7d72]">Connector posture</p>
              <CardTitle className="mt-2">Integration health</CardTitle>
            </div>
            <Badge tone={healthyIntegrationCount === integrations.length && integrations.length > 0 ? "healthy" : "medium"}>
              {healthyIntegrationCount}/{integrations.length || 0} healthy
            </Badge>
          </CardHeader>
          <CardContent className="space-y-3">
            {integrations.length ? (
              integrations.map((integration) => (
                <div key={integration.id} className="rounded-[24px] border border-black/8 bg-white/70 p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="font-semibold text-[#111111]">{integration.name}</p>
                      <p className="mt-2 text-sm leading-6 text-[#6d635a]">{truncate(integration.description ?? "Telemetry connector", 92)}</p>
                    </div>
                    <Badge tone={integration.health_status}>{integration.health_status}</Badge>
                  </div>
                  <p className="mt-4 text-[11px] uppercase tracking-[0.24em] text-[#8a7d72]">
                    Last sync {integration.last_synced_at ? formatDate(integration.last_synced_at) : "not yet recorded"}
                  </p>
                </div>
              ))
            ) : (
              <p className="text-sm leading-6 text-[#6d635a]">Integration health will appear here once telemetry sources are active.</p>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <CardHeader>
            <div>
              <p className="text-[11px] uppercase tracking-[0.28em] text-[#8a7d72]">Triage focus</p>
              <CardTitle className="mt-2">Active alert queue</CardTitle>
            </div>
            <Button asChild variant="outline" size="sm">
              <Link href="/alerts">
                Open alerts
                <ArrowUpRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent className="space-y-3">
            {topAlerts.length ? (
              topAlerts.map((alert) => (
                <Link
                  key={alert.id}
                  href={`/alerts/${alert.id}`}
                  className="block rounded-[24px] border border-black/8 bg-white/70 p-4 transition hover:border-[#ffb37f] hover:bg-white"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="max-w-2xl">
                      <p className="font-semibold tracking-[-0.02em] text-[#111111]">{alert.title}</p>
                      <p className="mt-2 text-sm leading-6 text-[#6d635a]">{truncate(alert.explanation_summary ?? alert.description ?? "No summary available.", 120)}</p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge tone={alert.severity.toLowerCase()}>{alert.severity}</Badge>
                      <Badge tone={scoreTone(alert.risk_score)}>{alert.risk_score.toFixed(1)}</Badge>
                    </div>
                  </div>
                  <div className="mt-4 flex flex-wrap items-center gap-2 text-sm text-[#8a7d72]">
                    <span>{toTitleCase(alert.source)}</span>
                    <span className="text-[#d0c5bc]">•</span>
                    <span>{alert.asset?.hostname ?? "Unassigned asset"}</span>
                    <span className="text-[#d0c5bc]">•</span>
                    <span>{formatDate(alert.occurred_at)}</span>
                  </div>
                </Link>
              ))
            ) : (
              <p className="text-sm leading-6 text-[#6d635a]">Open alert cards will appear here once the triage queue has active items.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div>
              <p className="text-[11px] uppercase tracking-[0.28em] text-[#8a7d72]">Activity stream</p>
              <CardTitle className="mt-2">Recent operational events</CardTitle>
            </div>
            <Badge tone="medium">Analyst-facing</Badge>
          </CardHeader>
          <CardContent className="space-y-3">
            {summary.recent_activity.map((entry) => (
              <div key={entry.id} className="rounded-[24px] border border-black/8 bg-white/70 p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="font-semibold text-[#111111]">{entry.title}</p>
                    <p className="mt-2 text-sm leading-6 text-[#6d635a]">{truncate(entry.summary, 104)}</p>
                  </div>
                  <Badge tone={entry.kind === "incident" ? "high" : "medium"}>{entry.kind}</Badge>
                </div>
                <p className="mt-4 text-[11px] uppercase tracking-[0.24em] text-[#8a7d72]">{formatDate(entry.timestamp)}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <CardHeader>
            <div>
              <p className="text-[11px] uppercase tracking-[0.28em] text-[#8a7d72]">Risk perimeter</p>
              <CardTitle className="mt-2">Assets demanding attention</CardTitle>
            </div>
            <Badge tone="high">Top priority hosts</Badge>
          </CardHeader>
          <CardContent className="space-y-3">
            {summary.risky_assets.map((asset) => (
              <Link
                key={asset.id}
                href={`/assets/${asset.id}`}
                className="block rounded-[24px] border border-black/8 bg-white/70 p-4 transition hover:border-[#ffb37f] hover:bg-white"
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-semibold text-[#111111]">{asset.hostname}</p>
                    <p className="mt-1 text-sm text-[#6d635a]">{asset.ip_address ?? "IP unavailable"}</p>
                  </div>
                  <Badge tone={scoreTone(asset.risk_score)}>{asset.risk_score.toFixed(1)}</Badge>
                </div>
                <p className="mt-3 text-sm leading-6 text-[#6d635a]">{asset.risk_summary ?? "No current risk summary."}</p>
              </Link>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div>
              <p className="text-[11px] uppercase tracking-[0.28em] text-[#8a7d72]">Analyst load</p>
              <CardTitle className="mt-2">Exposure and case distribution</CardTitle>
            </div>
            <Badge tone="medium">Assignee balance</Badge>
          </CardHeader>
          <CardContent className="space-y-5">
            {userExposure.length ? (
              <>
                <ComparisonBarChart data={userExposure} dataKey="total" />
                <div className="grid gap-3">
                  {userExposure.map((entry) => (
                    <div key={entry.label} className="flex items-center justify-between rounded-[20px] border border-black/8 bg-white/70 px-4 py-3">
                      <span className="font-medium text-[#171513]">{entry.label}</span>
                      <Badge tone={entry.total >= 4 ? "high" : "medium"}>{entry.total} active cases</Badge>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <p className="text-sm leading-6 text-[#6d635a]">User exposure will appear when alerts or incidents are assigned to analysts.</p>
            )}

            {incidentStatus.length ? (
              <div className="grid gap-3 border-t border-black/6 pt-5">
                {incidentStatus.map((entry) => (
                  <div key={entry.name} className="flex items-center justify-between rounded-[20px] border border-black/8 bg-white/70 px-4 py-3">
                    <span className="font-medium capitalize text-[#171513]">{entry.name}</span>
                    <Badge tone={entry.name}>{formatNumber(entry.value)}</Badge>
                  </div>
                ))}
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div>
            <p className="text-[11px] uppercase tracking-[0.28em] text-[#8a7d72]">Source comparison</p>
            <CardTitle className="mt-2">Alert volume by telemetry source</CardTitle>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="medium">
              <Sparkles className="mr-1 h-3.5 w-3.5" />
              Analyst narrative
            </Badge>
            <Badge tone="high">
              <ShieldAlert className="mr-1 h-3.5 w-3.5" />
              Risk-informed
            </Badge>
            <Badge tone="healthy">
              <Workflow className="mr-1 h-3.5 w-3.5" />
              Explainable
            </Badge>
            <Badge tone="low">
              <Activity className="mr-1 h-3.5 w-3.5" />
              Live telemetry
            </Badge>
            <Badge tone="medium">
              <Radar className="mr-1 h-3.5 w-3.5" />
              Presentation ready
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <ComparisonBarChart data={sourceComparison.length ? sourceComparison : [{ label: "No data", count: 0 }]} dataKey="count" />
        </CardContent>
      </Card>
    </div>
  );
}
