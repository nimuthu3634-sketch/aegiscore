import { useEffect, useState } from "react";

import { AnomalyScoreBadge } from "@/components/AnomalyScoreBadge";
import { ChartCard } from "@/components/ChartCard";
import { DataTable, type DataTableColumn } from "@/components/DataTable";
import {
  AlertTriangleIcon,
  ArrowUpRightIcon,
  IncidentIcon,
  ReportIcon,
  ShieldIcon,
} from "@/components/Icons";
import { SectionCard } from "@/components/SectionCard";
import { SeverityBadge } from "@/components/SeverityBadge";
import { StatCard } from "@/components/StatCard";
import { StatusBadge } from "@/components/StatusBadge";
import { useAuth } from "@/hooks/useAuth";
import { useRealtime } from "@/hooks/useRealtime";
import {
  fetchDashboardAnomalySummary,
  fetchDashboardCharts,
  fetchDashboardRecentAlerts,
  fetchDashboardRecentIncidents,
  fetchDashboardSummary,
} from "@/services/api";
import type {
  DashboardAnomalySummaryResponse,
  DashboardChartsResponse,
  DashboardRecentAlert,
  DashboardRecentIncident,
  DashboardSummaryResponse,
  SourceToolKey,
} from "@/types/domain";

type DashboardState = {
  summary: DashboardSummaryResponse;
  charts: DashboardChartsResponse;
  anomalySummary: DashboardAnomalySummaryResponse;
  recentAlerts: DashboardRecentAlert[];
  recentIncidents: DashboardRecentIncident[];
};

const statIcons = [
  <ShieldIcon key="shield" className="h-5 w-5" />,
  <AlertTriangleIcon key="alert" className="h-5 w-5" />,
  <IncidentIcon key="incident" className="h-5 w-5" />,
  <ReportIcon key="report" className="h-5 w-5" />,
];

const toolLabels: Record<SourceToolKey, string> = {
  wazuh: "Wazuh",
  suricata: "Suricata",
  nmap: "Nmap",
  hydra: "Hydra",
  virtualbox: "VirtualBox",
};

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatToolName(tool: SourceToolKey) {
  return toolLabels[tool];
}

function formatSeverityLabel(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

const recentAlertColumns: DataTableColumn<DashboardRecentAlert>[] = [
  {
    key: "title",
    header: "Alert",
    render: (alert) => (
      <div>
        <p className="font-semibold text-brand-black">{alert.title}</p>
        <p className="mt-1 text-xs text-brand-black/50">
          {formatToolName(alert.source_tool)} on {alert.source}
        </p>
      </div>
    ),
  },
  {
    key: "severity",
    header: "Severity",
    render: (alert) => <SeverityBadge level={alert.severity} />,
  },
  {
    key: "ai_score",
    header: "AI score",
    render: (alert) => <AnomalyScoreBadge score={alert.anomaly_score} compact />,
  },
  {
    key: "status",
    header: "Status",
    render: (alert) => (
      <StatusBadge variant={alert.status}>{alert.status.replace("_", " ")}</StatusBadge>
    ),
  },
  {
    key: "created_at",
    header: "Detected",
    render: (alert) => <span>{formatDateTime(alert.created_at)}</span>,
  },
];

const anomalousAlertColumns: DataTableColumn<DashboardRecentAlert>[] = [
  {
    key: "title",
    header: "Top anomalous event",
    render: (alert) => (
      <div>
        <p className="font-semibold text-brand-black">{alert.title}</p>
        <p className="mt-1 text-xs text-brand-black/50">
          {formatToolName(alert.source_tool)} on {alert.source}
        </p>
      </div>
    ),
  },
  {
    key: "score",
    header: "AI score",
    render: (alert) => <AnomalyScoreBadge score={alert.anomaly_score} />,
  },
  {
    key: "explanation",
    header: "Explanation",
    render: (alert) => (
      <span className="text-sm text-brand-black/70">{alert.anomaly_explanation}</span>
    ),
  },
];

function DashboardLoadingState() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {["orange", "critical", "dark", "success"].map((tone, index) => (
          <StatCard
            key={tone}
            label={["Total Alerts", "Critical Alerts", "Open Incidents", "Resolved Incidents"][index]}
            value="--"
            change="Loading live metrics"
            helper="Connecting to the dashboard feed"
            tone={tone as "orange" | "critical" | "dark" | "success"}
            icon={statIcons[index]}
          />
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.45fr_0.95fr]">
        <SectionCard
          title="Loading chart data"
          description="Preparing the latest alert trends and severity distribution."
        >
          <div className="h-72 animate-pulse rounded-[1.5rem] bg-brand-light/70" />
        </SectionCard>

        <div className="grid gap-6">
          <SectionCard
            title="Loading severity view"
            description="Fetching the current alert distribution."
          >
            <div className="h-32 animate-pulse rounded-[1.5rem] bg-brand-light/70" />
          </SectionCard>

          <SectionCard
            title="Loading source tool view"
            description="Fetching integration activity distribution."
          >
            <div className="h-32 animate-pulse rounded-[1.5rem] bg-brand-light/70" />
          </SectionCard>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <SectionCard title="Loading AI insights" description="Scoring the latest event baseline.">
          <div className="h-64 animate-pulse rounded-[1.5rem] bg-brand-light/70" />
        </SectionCard>

        <SectionCard
          title="Loading anomalous events"
          description="Preparing the most unusual alert patterns."
        >
          <div className="h-64 animate-pulse rounded-[1.5rem] bg-brand-light/70" />
        </SectionCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.45fr_0.95fr]">
        <SectionCard
          title="Loading recent alerts"
          description="Pulling the latest alert queue from the backend."
        >
          <div className="h-72 animate-pulse rounded-[1.5rem] bg-brand-light/70" />
        </SectionCard>

        <SectionCard
          title="Loading recent incidents"
          description="Pulling the latest incident activity."
        >
          <div className="h-72 animate-pulse rounded-[1.5rem] bg-brand-light/70" />
        </SectionCard>
      </div>
    </div>
  );
}

function DashboardErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <SectionCard
      title="Dashboard feed unavailable"
      description="The live dashboard endpoints could not be loaded for this session."
      action={
        <button type="button" onClick={onRetry} className="btn-primary">
          Retry dashboard
        </button>
      }
    >
      <div className="rounded-[1.5rem] border border-red-200 bg-red-50 px-4 py-5 text-sm text-red-700">
        {message}
      </div>
    </SectionCard>
  );
}

export function DashboardPage() {
  const { token } = useAuth();
  const { refreshVersion } = useRealtime();
  const [dashboard, setDashboard] = useState<DashboardState | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    if (!token) {
      return;
    }

    let isActive = true;
    setIsLoading(true);
    setError(null);

    void Promise.all([
      fetchDashboardSummary(token),
      fetchDashboardCharts(token),
      fetchDashboardAnomalySummary(token),
      fetchDashboardRecentAlerts(token),
      fetchDashboardRecentIncidents(token),
    ])
      .then(([summary, charts, anomalySummary, recentAlerts, recentIncidents]) => {
        if (!isActive) {
          return;
        }

        setDashboard({
          summary,
          charts,
          anomalySummary,
          recentAlerts,
          recentIncidents,
        });
      })
      .catch((requestError: unknown) => {
        if (!isActive) {
          return;
        }

        setError(
          requestError instanceof Error
            ? requestError.message
            : "The dashboard feed could not be loaded.",
        );
      })
      .finally(() => {
        if (isActive) {
          setIsLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [token, reloadKey, refreshVersion]);

  const handleRetry = () => {
    setReloadKey((currentValue) => currentValue + 1);
  };

  return (
    <div className="space-y-6">
      <SectionCard
        title="Command overview"
        description="Live dashboard data now combines operational metrics with a simple explainable anomaly model so analysts can present suspicious patterns alongside the normal SOC view."
        eyebrow="Dashboard"
        tone="dark"
        action={
          <button
            type="button"
            onClick={handleRetry}
            className="btn-primary inline-flex items-center gap-2"
            disabled={isLoading}
          >
            {isLoading ? "Refreshing..." : "Refresh live snapshot"}
            <ArrowUpRightIcon className="h-4 w-4" />
          </button>
        }
      >
        <div className="grid gap-4 lg:grid-cols-[1.25fr_0.75fr]">
          <div className="rounded-[1.5rem] border border-brand-white/10 bg-brand-white/5 p-5">
            <p className="text-sm font-semibold text-white">Presentation focus</p>
            <p className="mt-2 text-sm leading-6 text-brand-muted">
              Highlight real summary counts, alert patterns, anomaly scoring, and incident posture
              while keeping all data limited to safe, lab-only monitoring and simulation artifacts.
            </p>
          </div>

          <div className="rounded-[1.5rem] border border-brand-white/10 bg-brand-white/5 p-5">
            <p className="text-sm font-semibold text-white">Feed status</p>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <StatusBadge variant={error ? "degraded" : "connected"}>
                {error ? "refresh issue" : "live api connected"}
              </StatusBadge>
              {isLoading ? <StatusBadge variant="pending">refreshing</StatusBadge> : null}
            </div>
            <p className="mt-3 text-sm leading-6 text-brand-muted">
              Dashboard widgets read from authenticated FastAPI endpoints for summary, charts,
              recent queue activity, and anomaly insights.
            </p>
          </div>
        </div>
      </SectionCard>

      {!dashboard && isLoading ? <DashboardLoadingState /> : null}

      {!dashboard && error ? <DashboardErrorState message={error} onRetry={handleRetry} /> : null}

      {dashboard ? (
        <>
          {error ? (
            <div className="rounded-[1.5rem] border border-amber-200 bg-amber-50 px-4 py-4 text-sm text-amber-800">
              The latest refresh failed. Showing the most recent successful dashboard snapshot.
            </div>
          ) : null}

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <StatCard
              label="Total Alerts"
              value={dashboard.summary.total_alerts.toString()}
              change={`${dashboard.recentAlerts.length} latest queued`}
              helper="Across all seeded lab telemetry sources"
              tone="orange"
              icon={statIcons[0]}
            />
            <StatCard
              label="Critical Alerts"
              value={dashboard.summary.critical_alerts.toString()}
              change={`${Math.round(
                dashboard.summary.total_alerts > 0
                  ? (dashboard.summary.critical_alerts / dashboard.summary.total_alerts) * 100
                  : 0,
              )}% of volume`}
              helper="Highest-priority signals needing analyst attention"
              tone="critical"
              icon={statIcons[1]}
            />
            <StatCard
              label="Open Incidents"
              value={dashboard.summary.open_incidents.toString()}
              change={`${dashboard.recentIncidents.filter((incident) => incident.status !== "resolved").length} active in recent feed`}
              helper="Cases that remain open, triaged, or in progress"
              tone="dark"
              icon={statIcons[2]}
            />
            <StatCard
              label="Resolved Incidents"
              value={dashboard.summary.resolved_incidents.toString()}
              change={`${dashboard.recentIncidents.filter((incident) => incident.status === "resolved").length} recently closed`}
              helper="Ready for reporting and presentation follow-up"
              tone="success"
              icon={statIcons[3]}
            />
          </div>

          <div className="grid gap-6 xl:grid-cols-[1.45fr_0.95fr]">
            <ChartCard
              title="Alerts over time"
              description="Daily alert volume over the latest seven-day presentation window."
              data={dashboard.charts.alerts_over_time.map((point) => ({
                name: point.label,
                total: point.total,
              }))}
              xKey="name"
              yKey="total"
            />

            <div className="grid gap-6">
              <ChartCard
                title="Alerts by severity"
                description="Current priority distribution across the seeded alert queue."
                data={dashboard.charts.alerts_by_severity.map((point) => ({
                  label: formatSeverityLabel(point.severity),
                  count: point.count,
                }))}
                xKey="label"
                yKey="count"
                variant="bar"
              />

              <ChartCard
                title="Alerts by source tool"
                description="Signal volume split across telemetry sources and lab imports."
                data={dashboard.charts.alerts_by_source_tool.map((point) => ({
                  label: formatToolName(point.source_tool),
                  count: point.count,
                }))}
                xKey="label"
                yKey="count"
                variant="bar"
              />
            </div>
          </div>

          <div className="grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
            <SectionCard
              title="AI insights"
              description="Isolation Forest scores each alert using simple engineered features from severity, timing, source frequency, and service activity."
            >
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Model</p>
                  <p className="mt-3 text-xl font-semibold text-brand-black">
                    {dashboard.anomalySummary.model_name}
                  </p>
                  <p className="mt-2 text-sm text-brand-black/65">
                    Trained on {dashboard.anomalySummary.trained_on_events} demo events
                  </p>
                </div>

                <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">
                    Avg. anomaly score
                  </p>
                  <p className="mt-3 text-xl font-semibold text-brand-black">
                    {Math.round(dashboard.anomalySummary.average_anomaly_score * 100)}%
                  </p>
                  <p className="mt-2 text-sm text-brand-black/65">
                    Latest scoring pass {formatDateTime(dashboard.anomalySummary.trained_at)}
                  </p>
                </div>

                <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">
                    Alerts flagged
                  </p>
                  <p className="mt-3 text-xl font-semibold text-brand-black">
                    {dashboard.anomalySummary.anomalous_alert_count}
                  </p>
                  <p className="mt-2 text-sm text-brand-black/65">
                    Marked above the demo anomaly threshold
                  </p>
                </div>

                <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">
                    High anomaly alerts
                  </p>
                  <p className="mt-3 text-xl font-semibold text-brand-black">
                    {dashboard.anomalySummary.high_anomaly_alert_count}
                  </p>
                  <p className="mt-2 text-sm text-brand-black/65">
                    Score of 70% or above
                  </p>
                </div>
              </div>

              <div className="mt-4 rounded-[1.5rem] border border-brand-orange/15 bg-brand-orange/5 px-4 py-4 text-sm leading-6 text-brand-black/72">
                Feature set: {dashboard.anomalySummary.feature_labels.join(", ")}.
              </div>
            </SectionCard>

            <SectionCard
              title="Top anomalous events"
              description="Most unusual alerts currently in the queue, with simple explanation text for project demonstrations."
            >
              <DataTable
                columns={anomalousAlertColumns}
                rows={dashboard.anomalySummary.top_anomalous_alerts}
                rowKey={(alert) => alert.id}
                emptyMessage="No anomalous events are currently available."
              />
            </SectionCard>
          </div>

          <div className="grid gap-6 xl:grid-cols-[1.45fr_0.95fr]">
            <SectionCard
              title="Recent alerts"
              description="Most recent signals currently entering the investigation queue."
              action={
                <button type="button" className="btn-secondary">
                  View all alerts
                </button>
              }
            >
              <DataTable
                columns={recentAlertColumns}
                rows={dashboard.recentAlerts}
                rowKey={(alert) => alert.id}
              />
            </SectionCard>

            <SectionCard
              title="Recent incidents"
              description="Current incident activity sourced from the backend case feed."
            >
              <div className="space-y-4">
                {dashboard.recentIncidents.map((incident) => {
                  const assignmentVariant = incident.analyst_name ? "assigned" : "unassigned";

                  return (
                    <div
                      key={incident.id}
                      className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold text-brand-black">{incident.title}</p>
                          <p className="mt-1 text-xs text-brand-black/55">
                            {incident.id} - {incident.affected_asset}
                          </p>
                        </div>
                        <SeverityBadge level={incident.priority} />
                      </div>

                      <p className="mt-3 text-sm leading-6 text-brand-black/70">
                        {incident.summary}
                      </p>

                      <div className="mt-4 flex flex-wrap items-center gap-2">
                        <StatusBadge variant={incident.status}>
                          {incident.status.replace("_", " ")}
                        </StatusBadge>
                        <StatusBadge variant={assignmentVariant}>{assignmentVariant}</StatusBadge>
                      </div>

                      <p className="mt-3 text-xs text-brand-black/50">
                        Analyst: {incident.analyst_name ?? "Unassigned"} - Updated{" "}
                        {formatDateTime(incident.updated_at)}
                      </p>
                    </div>
                  );
                })}
              </div>
            </SectionCard>
          </div>
        </>
      ) : null}
    </div>
  );
}
