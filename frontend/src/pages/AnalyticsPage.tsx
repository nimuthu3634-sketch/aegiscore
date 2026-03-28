import { useEffect, useState } from "react";

import { AnomalyScoreBadge } from "@/components/AnomalyScoreBadge";
import { ChartCard } from "@/components/ChartCard";
import { DataTable, type DataTableColumn } from "@/components/DataTable";
import {
  AlertTriangleIcon,
  IncidentIcon,
  ReportIcon as AnalyticsIcon,
  ShieldIcon,
} from "@/components/Icons";
import { SectionCard } from "@/components/SectionCard";
import { SeverityBadge } from "@/components/SeverityBadge";
import { StatCard } from "@/components/StatCard";
import { StatusBadge } from "@/components/StatusBadge";
import { useAuth } from "@/hooks/useAuth";
import {
  fetchAlerts,
  fetchDashboardAnomalySummary,
  fetchDashboardCharts,
  fetchDashboardSummary,
  fetchIncidents,
} from "@/services/api";
import type {
  AlertApiRecord,
  DashboardAnomalySummaryResponse,
  DashboardChartsResponse,
  DashboardSummaryResponse,
  IncidentApiRecord,
  IncidentStatus,
  SourceToolKey,
} from "@/types/domain";

type AnalyticsState = {
  summary: DashboardSummaryResponse;
  charts: DashboardChartsResponse;
  anomalySummary: DashboardAnomalySummaryResponse;
  incidents: IncidentApiRecord[];
  latestAlerts: AlertApiRecord[];
};

const toolLabels: Record<SourceToolKey, string> = {
  wazuh: "Wazuh",
  suricata: "Suricata",
  nmap: "Nmap",
  hydra: "Hydra",
};

const incidentStatusOrder: IncidentStatus[] = ["open", "triaged", "in_progress", "resolved"];

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

function formatIncidentStatus(value: IncidentStatus) {
  return value.replace(/_/g, " ");
}

function buildIncidentStatusChart(incidents: IncidentApiRecord[]) {
  return incidentStatusOrder.map((status) => ({
    label: formatIncidentStatus(status),
    count: incidents.filter((incident) => incident.status === status).length,
  }));
}

const anomalousAlertColumns: DataTableColumn<AlertApiRecord>[] = [
  {
    key: "title",
    header: "Alert",
    render: (alert) => (
      <div>
        <p className="font-semibold text-brand-black">{alert.title}</p>
        <p className="mt-1 text-xs text-brand-black/55">
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
    key: "score",
    header: "AI score",
    render: (alert) => <AnomalyScoreBadge score={alert.anomaly_score} compact />,
  },
  {
    key: "created_at",
    header: "Detected",
    render: (alert) => <span>{formatDateTime(alert.created_at)}</span>,
  },
];

const incidentColumns: DataTableColumn<IncidentApiRecord>[] = [
  {
    key: "title",
    header: "Incident",
    render: (incident) => (
      <div>
        <p className="font-semibold text-brand-black">{incident.title}</p>
        <p className="mt-1 text-xs text-brand-black/55">{incident.affected_asset}</p>
      </div>
    ),
  },
  {
    key: "status",
    header: "Status",
    render: (incident) => (
      <StatusBadge variant={incident.status}>{formatIncidentStatus(incident.status)}</StatusBadge>
    ),
  },
  {
    key: "priority",
    header: "Priority",
    render: (incident) => <SeverityBadge level={incident.priority} />,
  },
  {
    key: "assignee",
    header: "Owner",
    render: (incident) => <span>{incident.assigned_to_name ?? "Needs assignment"}</span>,
  },
];

export function AnalyticsPage() {
  const { token } = useAuth();
  const [analyticsState, setAnalyticsState] = useState<AnalyticsState | null>(null);
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
      fetchIncidents(token),
      fetchAlerts(token, { page: 1, page_size: 6 }),
    ])
      .then(([summary, charts, anomalySummary, incidents, alerts]) => {
        if (!isActive) {
          return;
        }

        setAnalyticsState({
          summary,
          charts,
          anomalySummary,
          incidents: incidents.items,
          latestAlerts: alerts.items,
        });
      })
      .catch((requestError: unknown) => {
        if (!isActive) {
          return;
        }

        setError(
          requestError instanceof Error
            ? requestError.message
            : "The analytics workspace could not be loaded.",
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
  }, [token, reloadKey]);

  const summary = analyticsState?.summary ?? null;
  const charts = analyticsState?.charts ?? null;
  const anomalySummary = analyticsState?.anomalySummary ?? null;
  const incidents = analyticsState?.incidents ?? [];
  const openIncidents = incidents.filter((incident) => incident.status !== "resolved");
  const incidentStatusChart = buildIncidentStatusChart(incidents);

  return (
    <div className="space-y-6">
      <SectionCard
        title="Analytics workspace"
        description="Review explainable anomaly scoring, telemetry mix, and incident posture without the old reporting workflow."
        eyebrow="Analytics"
        tone="dark"
        action={
          <button
            type="button"
            onClick={() => setReloadKey((currentValue) => currentValue + 1)}
            className="btn-primary"
            disabled={isLoading}
          >
            {isLoading ? "Refreshing..." : "Refresh analytics"}
          </button>
        }
      >
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <StatCard
            label="Model"
            value={anomalySummary?.model_name ?? "--"}
            change={`${anomalySummary?.feature_labels.length ?? 0} features`}
            helper="Explainable anomaly detector"
            tone="orange"
            icon={<ShieldIcon className="h-5 w-5" />}
          />
          <StatCard
            label="Training Events"
            value={String(anomalySummary?.trained_on_events ?? "--")}
            change={anomalySummary?.trained_at ? formatDateTime(anomalySummary.trained_at) : "Awaiting training"}
            helper="Latest demo model refresh"
            tone="dark"
            icon={<AnalyticsIcon className="h-5 w-5" />}
          />
          <StatCard
            label="Anomalous Alerts"
            value={String(anomalySummary?.anomalous_alert_count ?? "--")}
            change={`${anomalySummary?.high_anomaly_alert_count ?? 0} high anomaly`}
            helper="Model-flagged unusual events"
            tone="critical"
            icon={<AlertTriangleIcon className="h-5 w-5" />}
          />
          <StatCard
            label="Open Incidents"
            value={String(summary?.open_incidents ?? "--")}
            change={`${openIncidents.length} active case${openIncidents.length === 1 ? "" : "s"}`}
            helper="Analyst follow-up still in progress"
            tone="success"
            icon={<IncidentIcon className="h-5 w-5" />}
          />
        </div>
      </SectionCard>

      {error ? (
        <div className="rounded-[1.5rem] border border-red-200 bg-red-50 px-4 py-4 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      {!analyticsState && isLoading ? (
        <div className="grid gap-6 xl:grid-cols-3">
          {["Severity mix", "Telemetry mix", "Incident posture"].map((title) => (
            <SectionCard key={title} title={`Loading ${title}`} description="Preparing analytics charts.">
              <div className="h-72 animate-pulse rounded-[1.5rem] bg-brand-light/70" />
            </SectionCard>
          ))}
        </div>
      ) : null}

      {analyticsState ? (
        <>
          <div className="grid gap-6 xl:grid-cols-3">
            <ChartCard
              title="Alerts by severity"
              description="Current alert severity distribution across the supported telemetry sources."
              data={(charts?.alerts_by_severity ?? []).map((item) => ({
                label: item.severity.charAt(0).toUpperCase() + item.severity.slice(1),
                count: item.count,
              }))}
              xKey="label"
              yKey="count"
              variant="bar"
            />
            <ChartCard
              title="Alerts by source tool"
              description="Supported data sources contributing to the current SOC view."
              data={(charts?.alerts_by_source_tool ?? []).map((item) => ({
                label: formatToolName(item.source_tool),
                count: item.count,
              }))}
              xKey="label"
              yKey="count"
              variant="bar"
            />
            <ChartCard
              title="Incident posture"
              description="Active analyst workload and case resolution mix."
              data={incidentStatusChart}
              xKey="label"
              yKey="count"
              variant="bar"
            />
          </div>

          <div className="grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
            <SectionCard
              title="Explainable anomaly summary"
              description="Keep the model readable for presentations by surfacing its key signals and output patterns."
            >
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Average score</p>
                  <p className="mt-3 text-xl font-semibold text-brand-black">
                    {Math.round((anomalySummary?.average_anomaly_score ?? 0) * 100)}%
                  </p>
                  <p className="mt-2 text-sm text-brand-black/65">
                    Average anomaly score across the current alert set
                  </p>
                </div>
                <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Critical alerts</p>
                  <p className="mt-3 text-xl font-semibold text-brand-black">
                    {summary?.critical_alerts ?? 0}
                  </p>
                  <p className="mt-2 text-sm text-brand-black/65">
                    Highest-priority alerts currently visible to analysts
                  </p>
                </div>
              </div>

              <div className="mt-4 rounded-[1.5rem] border border-brand-orange/15 bg-brand-orange/5 px-4 py-4 text-sm leading-6 text-brand-black/72">
                <strong>Feature labels:</strong> {anomalySummary?.feature_labels.join(", ") ?? "Unavailable"}.
              </div>

              <div className="mt-4 rounded-[1.5rem] border border-brand-black/8 bg-white p-4">
                <p className="text-sm font-semibold text-brand-black">Latest trained timestamp</p>
                <p className="mt-2 text-sm text-brand-black/68">
                  {anomalySummary?.trained_at
                    ? formatDateTime(anomalySummary.trained_at)
                    : "The demo model has not been trained yet."}
                </p>
              </div>
            </SectionCard>

            <SectionCard
              title="Top anomalous alerts"
              description="Highest-scoring unusual alerts for analyst review and presentation walkthroughs."
            >
              <DataTable
                columns={anomalousAlertColumns}
                rows={anomalySummary?.top_anomalous_alerts ?? analyticsState.latestAlerts}
                rowKey={(alert) => alert.id}
                emptyMessage="No anomalous alerts are available right now."
              />
            </SectionCard>
          </div>

          <SectionCard
            title="Active incident queue"
            description="Focused case list for the guided analyst workflow."
          >
            <DataTable
              columns={incidentColumns}
              rows={openIncidents}
              rowKey={(incident) => incident.id}
              emptyMessage="No active incidents are open at the moment."
            />
          </SectionCard>
        </>
      ) : null}
    </div>
  );
}
