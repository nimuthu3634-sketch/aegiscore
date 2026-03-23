import { useEffect, useMemo, useState } from "react";

import { AnomalyScoreBadge } from "@/components/AnomalyScoreBadge";
import { ChartCard } from "@/components/ChartCard";
import { DataTable, type DataTableColumn } from "@/components/DataTable";
import {
  AlertTriangleIcon,
  DownloadIcon,
  IncidentIcon,
  ReportIcon,
  ShieldIcon,
} from "@/components/Icons";
import { SectionCard } from "@/components/SectionCard";
import { SeverityBadge } from "@/components/SeverityBadge";
import { StatCard } from "@/components/StatCard";
import { StatusBadge } from "@/components/StatusBadge";
import { useAuth } from "@/hooks/useAuth";
import { fetchReports, fetchReportsSummary, generateReport } from "@/services/api";
import type { UserRole } from "@/types/auth";
import type {
  AlertApiRecord,
  ReportApiRecord,
  ReportFilters,
  ReportType,
  ReportsSummaryResponse,
  SourceToolKey,
} from "@/types/domain";

type ReportsState = {
  summary: ReportsSummaryResponse;
  reports: ReportApiRecord[];
};

const toolLabels: Record<SourceToolKey, string> = {
  wazuh: "Wazuh",
  suricata: "Suricata",
  nmap: "Nmap",
  hydra: "Hydra",
  lanl: "LANL",
  virtualbox: "VirtualBox",
};

const reportTypeOptions: Array<{ value: ReportType; label: string }> = [
  { value: "operations", label: "Operations" },
  { value: "executive", label: "Executive" },
  { value: "incident", label: "Incident" },
  { value: "analytics", label: "Analytics" },
];

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function toInputDate(value: Date) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function buildDefaultFilters(): Required<ReportFilters> {
  const endDate = new Date();
  const startDate = new Date(endDate);
  startDate.setDate(endDate.getDate() - 14);

  return {
    date_from: toInputDate(startDate),
    date_to: toInputDate(endDate),
  };
}

function formatStatusLabel(value: string) {
  return value.replace(/_/g, " ");
}

function formatSourceTool(tool: SourceToolKey) {
  return toolLabels[tool];
}

function formatReportType(value: ReportType) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function formatRangeLabel(dateFrom: string | null | undefined, dateTo: string | null | undefined) {
  if (dateFrom && dateTo) {
    return `${dateFrom} to ${dateTo}`;
  }

  if (dateFrom) {
    return `From ${dateFrom}`;
  }

  if (dateTo) {
    return `Through ${dateTo}`;
  }

  return "All available data";
}

function canGenerateReports(userRole: UserRole | undefined) {
  return userRole === "admin" || userRole === "analyst";
}

function downloadJson(filename: string, payload: unknown) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function ReportsLoadingState() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {["Reports Generated", "Alerts in Range", "Incidents in Range", "AI Flagged"].map((label) => (
          <StatCard
            key={label}
            label={label}
            value="--"
            change="Loading reporting feed"
            helper="Preparing reporting metrics"
            tone="orange"
            icon={<ReportIcon className="h-5 w-5" />}
          />
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        {["Severity", "Source tools", "Incident status"].map((title) => (
          <SectionCard key={title} title={`Loading ${title}`} description="Preparing chart data.">
            <div className="h-72 animate-pulse rounded-[1.5rem] bg-brand-light/70" />
          </SectionCard>
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.96fr_1.04fr]">
        <SectionCard title="Loading anomaly snapshot" description="Fetching AI insights.">
          <div className="h-72 animate-pulse rounded-[1.5rem] bg-brand-light/70" />
        </SectionCard>

        <SectionCard title="Loading report library" description="Fetching generated reports.">
          <div className="h-72 animate-pulse rounded-[1.5rem] bg-brand-light/70" />
        </SectionCard>
      </div>
    </div>
  );
}

function ReportsErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <SectionCard
      title="Reports feed unavailable"
      description="The reporting endpoints could not be loaded for this session."
      action={
        <button type="button" onClick={onRetry} className="btn-primary">
          Retry reports
        </button>
      }
    >
      <div className="rounded-[1.5rem] border border-red-200 bg-red-50 px-4 py-5 text-sm text-red-700">
        {message}
      </div>
    </SectionCard>
  );
}

export function ReportsPage() {
  const defaultFilters = useMemo(buildDefaultFilters, []);
  const { token, user } = useAuth();
  const [draftDateFrom, setDraftDateFrom] = useState(defaultFilters.date_from);
  const [draftDateTo, setDraftDateTo] = useState(defaultFilters.date_to);
  const [appliedFilters, setAppliedFilters] = useState<ReportFilters>(defaultFilters);
  const [reportType, setReportType] = useState<ReportType>("operations");
  const [reportTitle, setReportTitle] = useState("");
  const [reportsState, setReportsState] = useState<ReportsState | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    if (!token) {
      return;
    }

    let isActive = true;
    setIsLoading(true);
    setError(null);

    void Promise.all([
      fetchReportsSummary(token, appliedFilters),
      fetchReports(token, appliedFilters),
    ])
      .then(([summary, reports]) => {
        if (!isActive) {
          return;
        }

        setReportsState({ summary, reports });
      })
      .catch((requestError: unknown) => {
        if (!isActive) {
          return;
        }

        setError(
          requestError instanceof Error
            ? requestError.message
            : "The reports workspace could not be loaded.",
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
  }, [token, appliedFilters, reloadKey]);

  const canGenerate = canGenerateReports(user?.role);
  const summary = reportsState?.summary ?? null;
  const reports = reportsState?.reports ?? [];

  const reportColumns = useMemo<DataTableColumn<ReportApiRecord>[]>(
    () => [
      {
        key: "title",
        header: "Report",
        render: (report) => (
          <div>
            <p className="font-semibold text-brand-black">{report.title}</p>
            <p className="mt-1 text-xs text-brand-black/55">
              {formatReportType(report.report_type)} report
            </p>
          </div>
        ),
      },
      {
        key: "owner",
        header: "Owner",
        render: (report) => <span>{report.generated_by_name ?? "AegisCore Operations"}</span>,
      },
      {
        key: "range",
        header: "Coverage",
        render: (report) => (
          <span>
            {formatRangeLabel(
              report.content_json.date_range?.date_from,
              report.content_json.date_range?.date_to,
            )}
          </span>
        ),
      },
      {
        key: "status",
        header: "Status",
        render: (report) => <StatusBadge variant={report.status}>{report.status}</StatusBadge>,
      },
      {
        key: "created_at",
        header: "Generated",
        render: (report) => <span>{formatDateTime(report.created_at)}</span>,
      },
      {
        key: "export",
        header: "Export",
        render: (report) => (
          <button
            type="button"
            className="btn-secondary"
            onClick={() =>
              downloadJson(`${report.id}.json`, {
                id: report.id,
                title: report.title,
                report_type: report.report_type,
                status: report.status,
                created_at: report.created_at,
                content_json: report.content_json,
              })
            }
          >
            JSON
          </button>
        ),
      },
    ],
    [],
  );

  const anomalousAlertColumns = useMemo<DataTableColumn<AlertApiRecord>[]>(
    () => [
      {
        key: "title",
        header: "Alert",
        render: (alert) => (
          <div>
            <p className="font-semibold text-brand-black">{alert.title}</p>
            <p className="mt-1 text-xs text-brand-black/50">
              {formatSourceTool(alert.source_tool)} on {alert.source}
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
        key: "explanation",
        header: "Explanation",
        render: (alert) => (
          <span className="text-sm text-brand-black/70">{alert.anomaly_explanation}</span>
        ),
      },
    ],
    [],
  );

  const handleRetry = () => {
    setReloadKey((currentValue) => currentValue + 1);
  };

  const handleApplyFilters = () => {
    if (draftDateFrom && draftDateTo && draftDateFrom > draftDateTo) {
      setActionMessage("Start date cannot be later than end date.");
      return;
    }

    setActionMessage(null);
    setAppliedFilters({
      date_from: draftDateFrom || undefined,
      date_to: draftDateTo || undefined,
    });
  };

  const handleGenerateReport = async () => {
    if (!token || !canGenerate) {
      return;
    }

    setIsGenerating(true);
    setActionMessage(null);

    try {
      const report = await generateReport(token, {
        title: reportTitle.trim() || undefined,
        report_type: reportType,
        date_from: appliedFilters.date_from,
        date_to: appliedFilters.date_to,
      });

      setActionMessage(`Generated "${report.title}" and added it to the report library.`);
      setReportTitle("");
      setReloadKey((currentValue) => currentValue + 1);
    } catch (requestError) {
      setActionMessage(
        requestError instanceof Error
          ? requestError.message
          : "The report could not be generated.",
      );
    } finally {
      setIsGenerating(false);
    }
  };

  const handleExportSummary = () => {
    if (!summary) {
      return;
    }

    const rangeLabel = formatRangeLabel(summary.date_from, summary.date_to)
      .toLowerCase()
      .replace(/\s+/g, "-");
    downloadJson(`aegiscore-report-summary-${rangeLabel}.json`, summary);
  };

  const criticalAlertCount =
    summary?.alerts_by_severity.find((item) => item.severity === "critical")?.count ?? 0;
  const resolvedIncidentCount =
    summary?.incidents_by_status.find((item) => item.status === "resolved")?.count ?? 0;

  return (
    <div className="space-y-6">
      <SectionCard
        title="Reporting workspace"
        description="Create structured SOC summaries from live backend data using alert volume, incident posture, and explainable anomaly insights."
        eyebrow="Reports"
        tone="dark"
        action={
          <button
            type="button"
            onClick={handleRetry}
            className="btn-primary"
            disabled={isLoading}
          >
            {isLoading ? "Refreshing..." : "Refresh reports"}
          </button>
        }
      >
        <div className="grid gap-4 xl:grid-cols-4">
          <label className="block text-sm font-medium text-white">
            Start date
            <input
              type="date"
              value={draftDateFrom}
              onChange={(event) => setDraftDateFrom(event.target.value)}
              className="input-shell mt-2 w-full border-brand-white/10 bg-brand-white/5 text-white"
            />
          </label>

          <label className="block text-sm font-medium text-white">
            End date
            <input
              type="date"
              value={draftDateTo}
              onChange={(event) => setDraftDateTo(event.target.value)}
              className="input-shell mt-2 w-full border-brand-white/10 bg-brand-white/5 text-white"
            />
          </label>

          <label className="block text-sm font-medium text-white">
            Report type
            <select
              value={reportType}
              onChange={(event) => setReportType(event.target.value as ReportType)}
              className="input-shell mt-2 w-full border-brand-white/10 bg-brand-white/5 text-white"
            >
              {reportTypeOptions.map((option) => (
                <option key={option.value} value={option.value} className="text-brand-black">
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-sm font-medium text-white">
            Custom title
            <input
              type="text"
              value={reportTitle}
              onChange={(event) => setReportTitle(event.target.value)}
              placeholder="Optional report title"
              className="input-shell mt-2 w-full border-brand-white/10 bg-brand-white/5 text-white placeholder:text-brand-muted"
            />
          </label>
        </div>

        <div className="mt-5 flex flex-col gap-3 lg:flex-row">
          <button type="button" onClick={handleApplyFilters} className="btn-secondary">
            Apply date range
          </button>
          <button
            type="button"
            onClick={handleGenerateReport}
            className="btn-primary"
            disabled={!canGenerate || isGenerating}
          >
            {isGenerating ? "Generating..." : "Generate report"}
          </button>
          <button
            type="button"
            onClick={handleExportSummary}
            className="btn-secondary inline-flex items-center gap-2"
            disabled={!summary}
          >
            <DownloadIcon className="h-4 w-4" />
            Export summary JSON
          </button>
        </div>

        <div className="mt-5 grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
          <div className="rounded-[1.5rem] border border-brand-white/10 bg-brand-white/5 p-5">
            <p className="text-sm font-semibold text-white">Selected reporting window</p>
            <p className="mt-2 text-sm leading-6 text-brand-muted">
              {formatRangeLabel(appliedFilters.date_from ?? null, appliedFilters.date_to ?? null)}.
              This snapshot combines live alert counts, source coverage, incident status, and AI
              anomaly indicators for the current selected range.
            </p>
          </div>

          <div className="rounded-[1.5rem] border border-brand-white/10 bg-brand-white/5 p-5">
            <p className="text-sm font-semibold text-white">Generation access</p>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <StatusBadge variant={canGenerate ? "connected" : "pending"}>
                {canGenerate ? "generate enabled" : "read-only"}
              </StatusBadge>
              {isGenerating ? <StatusBadge variant="pending">building report</StatusBadge> : null}
            </div>
            <p className="mt-3 text-sm leading-6 text-brand-muted">
              Admin and analyst roles can generate stored report snapshots. Viewer accounts can
              still review summaries and export JSON as needed.
            </p>
          </div>
        </div>
      </SectionCard>

      {actionMessage ? (
        <div className="rounded-[1.5rem] border border-brand-orange/15 bg-brand-orange/5 px-4 py-4 text-sm text-brand-black/75">
          {actionMessage}
        </div>
      ) : null}

      {!reportsState && isLoading ? <ReportsLoadingState /> : null}

      {!reportsState && error ? <ReportsErrorState message={error} onRetry={handleRetry} /> : null}

      {reportsState ? (
        <>
          {error ? (
            <div className="rounded-[1.5rem] border border-amber-200 bg-amber-50 px-4 py-4 text-sm text-amber-800">
              The latest refresh failed. Showing the most recent successful report snapshot.
            </div>
          ) : null}

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <StatCard
              label="Reports Generated"
              value={summary?.reports_generated.toString() ?? "--"}
              change={`${summary?.ready_reports ?? 0} ready`}
              helper="Generated within the selected window"
              tone="orange"
              icon={<ReportIcon className="h-5 w-5" />}
            />
            <StatCard
              label="Alerts in Range"
              value={summary?.filtered_alert_count.toString() ?? "--"}
              change={`${criticalAlertCount} critical`}
              helper="Live alert volume included in this summary"
              tone="critical"
              icon={<AlertTriangleIcon className="h-5 w-5" />}
            />
            <StatCard
              label="Incidents in Range"
              value={summary?.filtered_incident_count.toString() ?? "--"}
              change={`${resolvedIncidentCount} resolved`}
              helper="Incident cases opened inside the reporting window"
              tone="dark"
              icon={<IncidentIcon className="h-5 w-5" />}
            />
            <StatCard
              label="AI Flagged"
              value={summary?.anomaly_summary.anomalous_alert_count.toString() ?? "--"}
              change={`${summary?.anomaly_summary.high_anomaly_alert_count ?? 0} high anomaly`}
              helper="Alerts marked as unusual by the anomaly model"
              tone="success"
              icon={<ShieldIcon className="h-5 w-5" />}
            />
          </div>

          <div className="grid gap-6 xl:grid-cols-3">
            <ChartCard
              title="Alerts by severity"
              description="Priority distribution for the current reporting window."
              data={(summary?.alerts_by_severity ?? []).map((item) => ({
                label: item.severity.charAt(0).toUpperCase() + item.severity.slice(1),
                count: item.count,
              }))}
              xKey="label"
              yKey="count"
              variant="bar"
            />

            <ChartCard
              title="Alerts by source tool"
              description="How the selected window is weighted across telemetry sources."
              data={(summary?.alerts_by_source_tool ?? []).map((item) => ({
                label: formatSourceTool(item.source_tool),
                count: item.count,
              }))}
              xKey="label"
              yKey="count"
              variant="bar"
            />

            <ChartCard
              title="Incidents by status"
              description="Current case disposition inside the selected reporting range."
              data={(summary?.incidents_by_status ?? []).map((item) => ({
                label: formatStatusLabel(item.status),
                count: item.count,
              }))}
              xKey="label"
              yKey="count"
              variant="bar"
            />
          </div>

          <div className="grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
            <SectionCard
              title="Anomaly summary"
              description="Explainable AI indicators that can be referenced directly in analyst review and reporting."
            >
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Model</p>
                  <p className="mt-3 text-xl font-semibold text-brand-black">
                    {summary?.anomaly_summary.model_name}
                  </p>
                  <p className="mt-2 text-sm text-brand-black/65">
                    Trained on {summary?.anomaly_summary.trained_on_events ?? 0} historical events
                  </p>
                </div>

                <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">
                    Avg. anomaly score
                  </p>
                  <p className="mt-3 text-xl font-semibold text-brand-black">
                    {Math.round((summary?.anomaly_summary.average_anomaly_score ?? 0) * 100)}%
                  </p>
                  <p className="mt-2 text-sm text-brand-black/65">
                    Latest model refresh{" "}
                    {summary?.anomaly_summary.trained_at
                      ? formatDateTime(summary.anomaly_summary.trained_at)
                      : "Unavailable"}
                  </p>
                </div>

                <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">
                    Alerts flagged
                  </p>
                  <p className="mt-3 text-xl font-semibold text-brand-black">
                    {summary?.anomaly_summary.anomalous_alert_count ?? 0}
                  </p>
                  <p className="mt-2 text-sm text-brand-black/65">
                    Above the baseline anomaly threshold
                  </p>
                </div>

                <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">
                    High anomaly alerts
                  </p>
                  <p className="mt-3 text-xl font-semibold text-brand-black">
                    {summary?.anomaly_summary.high_anomaly_alert_count ?? 0}
                  </p>
                  <p className="mt-2 text-sm text-brand-black/65">Scored at 70% or above</p>
                </div>
              </div>

              <div className="mt-4 rounded-[1.5rem] border border-brand-orange/15 bg-brand-orange/5 px-4 py-4 text-sm leading-6 text-brand-black/72">
                Feature set: {summary?.anomaly_summary.feature_labels.join(", ")}.
              </div>
            </SectionCard>

            <SectionCard
              title="Top anomalous alerts"
              description="Highest-scoring unusual events included in the current reporting window."
            >
              <DataTable
                columns={anomalousAlertColumns}
                rows={summary?.anomaly_summary.top_anomalous_alerts ?? []}
                rowKey={(alert) => alert.id}
                emptyMessage="No anomalous alerts fall inside the selected date range."
              />
            </SectionCard>
          </div>

          <SectionCard
            title="Generated reports"
            description={`${reports.length} report snapshots are currently available for export and review.`}
          >
            <DataTable
              columns={reportColumns}
              rows={reports}
              rowKey={(report) => report.id}
              emptyMessage="No reports have been generated for the selected date range yet."
            />
          </SectionCard>
        </>
      ) : null}
    </div>
  );
}
