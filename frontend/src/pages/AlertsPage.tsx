import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { AnomalyScoreBadge } from "@/components/AnomalyScoreBadge";
import { DataTable, type DataTableColumn } from "@/components/DataTable";
import { FilterIcon, SearchIcon } from "@/components/Icons";
import { SectionCard } from "@/components/SectionCard";
import { SeverityBadge } from "@/components/SeverityBadge";
import { StatusBadge } from "@/components/StatusBadge";
import { useAuth } from "@/hooks/useAuth";
import { useRealtime } from "@/hooks/useRealtime";
import {
  executeAlertResponseAction,
  fetchAlertById,
  fetchAlertResponseActions,
  fetchAlerts,
  patchAlertStatus,
} from "@/services/api";
import type { UserRole } from "@/types/auth";
import type {
  AlertApiRecord,
  AlertListResponse,
  AlertResponseActionsResponse,
  AlertStatus,
  ResponseActionRecord,
  ResponseActionType,
  SeverityLevel,
  SourceToolKey,
} from "@/types/domain";

const severityOptions: Array<{ value: "all" | SeverityLevel; label: string }> = [
  { value: "all", label: "All severities" },
  { value: "critical", label: "Critical" },
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
];

const statusOptions: Array<{ value: "all" | AlertStatus; label: string }> = [
  { value: "all", label: "All statuses" },
  { value: "new", label: "New" },
  { value: "triaged", label: "Triaged" },
  { value: "investigating", label: "Investigating" },
  { value: "resolved", label: "Resolved" },
];

const sourceToolOptions: Array<{ value: "all" | SourceToolKey; label: string }> = [
  { value: "all", label: "All sources" },
  { value: "wazuh", label: "Wazuh" },
  { value: "suricata", label: "Suricata" },
  { value: "nmap", label: "Nmap" },
  { value: "hydra", label: "Hydra" },
  { value: "virtualbox", label: "VirtualBox" },
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

function getSourceToolLabel(sourceTool: SourceToolKey) {
  return toolLabels[sourceTool];
}

function getSourceToolNote(sourceTool: SourceToolKey) {
  if (sourceTool === "nmap") {
    return "Imported lab assessment results only";
  }

  if (sourceTool === "hydra") {
    return "Imported lab credential assessment results only";
  }

  return null;
}

function canUpdateAlerts(userRole: UserRole | undefined) {
  return userRole === "admin" || userRole === "analyst";
}

function canManageIncidents(userRole: UserRole | undefined) {
  return userRole === "admin" || userRole === "analyst";
}

function getResponseActionLabel(actionType: ResponseActionType) {
  switch (actionType) {
    case "create_incident":
      return "Create incident";
    case "block_source_ip":
      return "Block source IP";
    case "isolate_asset":
      return "Isolate asset";
    case "disable_account":
      return "Disable account";
    case "mark_investigating":
      return "Move to investigating";
    default:
      return String(actionType).replace(/_/g, " ");
  }
}

function getResponseActionTone(action: ResponseActionRecord) {
  if (action.status === "completed") {
    return "bg-emerald-100 text-emerald-700 ring-emerald-200";
  }

  return "bg-amber-100 text-amber-700 ring-amber-200";
}

function getResponseModeTone(mode: ResponseActionRecord["execution_mode"]) {
  if (mode === "automated") {
    return "bg-sky-100 text-sky-700 ring-sky-200";
  }

  return "bg-brand-black/5 text-brand-black/70 ring-brand-black/10";
}

const alertColumns: DataTableColumn<AlertApiRecord>[] = [
  {
    key: "title",
    header: "Alert",
    render: (alert) => (
      <div>
        <p className="font-semibold text-brand-black">{alert.title}</p>
        <p className="mt-1 text-xs text-brand-black/55">{alert.source}</p>
      </div>
    ),
  },
  {
    key: "source_tool",
    header: "Source Tool",
    render: (alert) => (
      <div>
        <p className="font-medium text-brand-black">{getSourceToolLabel(alert.source_tool)}</p>
        {getSourceToolNote(alert.source_tool) ? (
          <p className="mt-1 text-xs text-brand-black/50">{getSourceToolNote(alert.source_tool)}</p>
        ) : null}
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

export function AlertsPage() {
  const navigate = useNavigate();
  const { token, user } = useAuth();
  const { refreshVersion } = useRealtime();
  const [alertsResponse, setAlertsResponse] = useState<AlertListResponse | null>(null);
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);
  const [selectedAlert, setSelectedAlert] = useState<AlertApiRecord | null>(null);
  const [statusDraft, setStatusDraft] = useState<AlertStatus>("new");
  const [searchQuery, setSearchQuery] = useState("");
  const [severityFilter, setSeverityFilter] = useState<"all" | SeverityLevel>("all");
  const [statusFilter, setStatusFilter] = useState<"all" | AlertStatus>("all");
  const [sourceToolFilter, setSourceToolFilter] = useState<"all" | SourceToolKey>("all");
  const [page, setPage] = useState(1);
  const [listLoading, setListLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [updateLoading, setUpdateLoading] = useState(false);
  const [listError, setListError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [updateMessage, setUpdateMessage] = useState<string | null>(null);
  const [responseActions, setResponseActions] = useState<AlertResponseActionsResponse | null>(null);
  const [responseActionsLoading, setResponseActionsLoading] = useState(false);
  const [responseActionsError, setResponseActionsError] = useState<string | null>(null);
  const [responseActionLoading, setResponseActionLoading] = useState<ResponseActionType | null>(null);
  const [responseActionMessage, setResponseActionMessage] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    if (!token) {
      return;
    }

    let isActive = true;
    setListLoading(true);
    setListError(null);

    void fetchAlerts(token, {
      search: searchQuery.trim() || undefined,
      severity: severityFilter === "all" ? undefined : severityFilter,
      status: statusFilter === "all" ? undefined : statusFilter,
      source_tool: sourceToolFilter === "all" ? undefined : sourceToolFilter,
      page,
      page_size: 8,
    })
      .then((response) => {
        if (!isActive) {
          return;
        }

        setAlertsResponse(response);
        setSelectedAlertId((currentId) => {
          if (response.items.length === 0) {
            return null;
          }

          if (currentId && response.items.some((alert) => alert.id === currentId)) {
            return currentId;
          }

          return response.items[0]?.id ?? null;
        });
      })
      .catch((requestError: unknown) => {
        if (!isActive) {
          return;
        }

        setListError(
          requestError instanceof Error ? requestError.message : "The alert list could not be loaded.",
        );
      })
      .finally(() => {
        if (isActive) {
          setListLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [token, searchQuery, severityFilter, statusFilter, sourceToolFilter, page, reloadKey, refreshVersion]);

  useEffect(() => {
    if (!token || !selectedAlertId) {
      setSelectedAlert(null);
      setDetailError(null);
      return;
    }

    let isActive = true;
    setDetailLoading(true);
    setDetailError(null);

    void fetchAlertById(token, selectedAlertId)
      .then((response) => {
        if (!isActive) {
          return;
        }

        setSelectedAlert(response);
        setStatusDraft(response.status);
      })
      .catch((requestError: unknown) => {
        if (!isActive) {
          return;
        }

        setDetailError(
          requestError instanceof Error ? requestError.message : "The alert detail could not be loaded.",
        );
      })
      .finally(() => {
        if (isActive) {
          setDetailLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [token, selectedAlertId, reloadKey, refreshVersion]);

  useEffect(() => {
    if (!token || !selectedAlertId) {
      setResponseActions(null);
      setResponseActionsError(null);
      return;
    }

    let isActive = true;
    setResponseActionsLoading(true);
    setResponseActionsError(null);

    void fetchAlertResponseActions(token, selectedAlertId)
      .then((response) => {
        if (!isActive) {
          return;
        }

        setResponseActions(response);
      })
      .catch((requestError: unknown) => {
        if (!isActive) {
          return;
        }

        setResponseActionsError(
          requestError instanceof Error
            ? requestError.message
            : "Response actions could not be loaded.",
        );
      })
      .finally(() => {
        if (isActive) {
          setResponseActionsLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [token, selectedAlertId, reloadKey, refreshVersion]);

  const handleRetry = () => {
    setReloadKey((currentValue) => currentValue + 1);
  };

  const handleStatusUpdate = async () => {
    if (!token || !selectedAlertId) {
      return;
    }

    setUpdateLoading(true);
    setUpdateMessage(null);

    try {
      const updatedAlert = await patchAlertStatus(token, selectedAlertId, { status: statusDraft });
      setSelectedAlert(updatedAlert);
      setUpdateMessage("Alert status updated successfully.");
      setReloadKey((currentValue) => currentValue + 1);
    } catch (requestError) {
      setUpdateMessage(
        requestError instanceof Error
          ? requestError.message
          : "The alert status could not be updated.",
      );
    } finally {
      setUpdateLoading(false);
    }
  };

  const handleExecuteResponseAction = async (actionType: ResponseActionType) => {
    if (!token || !selectedAlertId) {
      return;
    }

    setResponseActionLoading(actionType);
    setResponseActionMessage(null);

    try {
      const action = await executeAlertResponseAction(token, selectedAlertId, {
        action_type: actionType,
      });
      setResponseActionMessage(action.result_summary);
      setReloadKey((currentValue) => currentValue + 1);
    } catch (requestError) {
      setResponseActionMessage(
        requestError instanceof Error
          ? requestError.message
          : "The response action could not be completed.",
      );
    } finally {
      setResponseActionLoading(null);
    }
  };

  const totalPages = alertsResponse?.total_pages ?? 1;
  const totalItems = alertsResponse?.total_items ?? 0;
  const listItems = alertsResponse?.items ?? [];
  const selectedSourceNote = selectedAlert ? getSourceToolNote(selectedAlert.source_tool) : null;
  const canEditStatus = canUpdateAlerts(user?.role);
  const canRunResponseActions = canManageIncidents(user?.role);
  const recommendedActions = responseActions?.recommended_actions ?? [];
  const responseActionHistory = responseActions?.items ?? [];

  return (
    <div className="space-y-6">
      <SectionCard
        title="Alert investigation workspace"
        description="Search, filter, review, and update live alert records from the backend while pairing each event with a simple anomaly score and explanation."
        eyebrow="Alerts"
        action={
          <button type="button" onClick={handleRetry} className="btn-primary" disabled={listLoading}>
            {listLoading ? "Refreshing..." : "Refresh alerts"}
          </button>
        }
      >
        <div className="grid gap-4 xl:grid-cols-[1.4fr_0.9fr_0.9fr_0.9fr]">
          <label className="input-shell flex items-center gap-3">
            <SearchIcon className="h-4 w-4 text-brand-black/45" />
            <input
              type="text"
              value={searchQuery}
              onChange={(event) => {
                setSearchQuery(event.target.value);
                setPage(1);
              }}
              placeholder="Search title, description, source, or tool"
              className="w-full bg-transparent text-sm text-brand-black outline-none placeholder:text-brand-black/40"
            />
          </label>

          <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-brand-black">
              <FilterIcon className="h-4 w-4" />
              Severity
            </div>
            <select
              value={severityFilter}
              onChange={(event) => {
                setSeverityFilter(event.target.value as "all" | SeverityLevel);
                setPage(1);
              }}
              className="input-shell w-full bg-white"
            >
              {severityOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-brand-black">
              <FilterIcon className="h-4 w-4" />
              Status
            </div>
            <select
              value={statusFilter}
              onChange={(event) => {
                setStatusFilter(event.target.value as "all" | AlertStatus);
                setPage(1);
              }}
              className="input-shell w-full bg-white"
            >
              {statusOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-brand-black">
              <FilterIcon className="h-4 w-4" />
              Source Tool
            </div>
            <select
              value={sourceToolFilter}
              onChange={(event) => {
                setSourceToolFilter(event.target.value as "all" | SourceToolKey);
                setPage(1);
              }}
              className="input-shell w-full bg-white"
            >
              {sourceToolOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </SectionCard>

      <div className="grid gap-6 xl:grid-cols-[1.45fr_0.95fr]">
        <SectionCard
          title="Alert queue"
          description={`${totalItems} alerts match the current filters across the live backend feed.`}
        >
          {listError ? (
            <div className="space-y-4">
              <div className="rounded-[1.5rem] border border-red-200 bg-red-50 px-4 py-5 text-sm text-red-700">
                {listError}
              </div>
              <button type="button" onClick={handleRetry} className="btn-primary">
                Retry alert list
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {listLoading && !alertsResponse ? (
                <div className="h-80 animate-pulse rounded-[1.5rem] bg-brand-light/70" />
              ) : (
                <DataTable
                  columns={alertColumns}
                  rows={listItems}
                  rowKey={(alert) => alert.id}
                  compact
                  onRowClick={(alert) => setSelectedAlertId(alert.id)}
                  selectedRowKey={selectedAlertId ?? undefined}
                  emptyMessage="No alerts match the current filters."
                />
              )}

              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm text-brand-black/60">
                  Page {page} of {totalPages}
                </p>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setPage((currentValue) => Math.max(1, currentValue - 1))}
                    className="btn-secondary"
                    disabled={page === 1 || listLoading}
                  >
                    Previous
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      setPage((currentValue) => Math.min(totalPages, currentValue + 1))
                    }
                    className="btn-secondary"
                    disabled={page >= totalPages || listLoading}
                  >
                    Next
                  </button>
                </div>
              </div>
            </div>
          )}
        </SectionCard>

        <SectionCard
          title="Alert details"
          description="Focused context, AI insight, and workflow controls for the selected alert."
        >
          {!selectedAlertId && !listLoading ? (
            <div className="rounded-[1.5rem] border border-dashed border-brand-black/10 bg-brand-light/50 p-10 text-center text-sm text-brand-black/55">
              No alert is currently selected.
            </div>
          ) : detailLoading && !selectedAlert ? (
            <div className="h-80 animate-pulse rounded-[1.5rem] bg-brand-light/70" />
          ) : detailError ? (
            <div className="space-y-4">
              <div className="rounded-[1.5rem] border border-red-200 bg-red-50 px-4 py-5 text-sm text-red-700">
                {detailError}
              </div>
              <button type="button" onClick={handleRetry} className="btn-secondary">
                Retry detail
              </button>
            </div>
          ) : selectedAlert ? (
            <div className="space-y-4">
              <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-brand-orange">
                  {selectedAlert.id}
                </p>
                <h3 className="mt-2 text-xl font-semibold text-brand-black">
                  {selectedAlert.title}
                </h3>
                <p className="mt-3 text-sm leading-6 text-brand-black/70">
                  {selectedAlert.description}
                </p>
              </div>

              {selectedSourceNote ? (
                <div className="rounded-[1.5rem] border border-brand-orange/20 bg-brand-orange/5 px-4 py-4 text-sm text-brand-black/70">
                  {selectedSourceNote}. This alert is displayed as a safe imported assessment
                  artifact, not as an offensive automation workflow.
                </div>
              ) : null}

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-[1.5rem] border border-brand-black/8 bg-white p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Severity</p>
                  <div className="mt-3">
                    <SeverityBadge level={selectedAlert.severity} />
                  </div>
                </div>
                <div className="rounded-[1.5rem] border border-brand-black/8 bg-white p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Status</p>
                  <div className="mt-3">
                    <StatusBadge variant={selectedAlert.status}>
                      {selectedAlert.status.replace("_", " ")}
                    </StatusBadge>
                  </div>
                </div>
              </div>

              <div className="rounded-[1.5rem] border border-brand-black/8 bg-white p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-brand-black">AI anomaly insight</p>
                    <p className="mt-1 text-xs text-brand-black/55">
                      A simple Isolation Forest score built from event severity, timing, source frequency, and activity context.
                    </p>
                  </div>
                  <AnomalyScoreBadge score={selectedAlert.anomaly_score} />
                </div>

                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <div className="rounded-[1.25rem] bg-brand-light/60 p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Explanation</p>
                    <p className="mt-2 text-sm font-medium text-brand-black">
                      {selectedAlert.anomaly_explanation}
                    </p>
                  </div>
                  <div className="rounded-[1.25rem] bg-brand-light/60 p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Flag state</p>
                    <div className="mt-2">
                      <StatusBadge variant={selectedAlert.is_anomalous ? "degraded" : "connected"}>
                        {selectedAlert.is_anomalous ? "anomalous" : "within baseline"}
                      </StatusBadge>
                    </div>
                  </div>
                </div>
              </div>

              <div className="rounded-[1.5rem] border border-brand-black/8 bg-white p-4">
                <p className="text-sm font-semibold text-brand-black">Context</p>
                <dl className="mt-4 space-y-3 text-sm text-brand-black/70">
                  <div className="flex justify-between gap-4">
                    <dt>Source Tool</dt>
                    <dd>{getSourceToolLabel(selectedAlert.source_tool)}</dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt>Source Asset</dt>
                    <dd>{selectedAlert.source}</dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt>Analyst confidence</dt>
                    <dd>{Math.round(selectedAlert.confidence_score * 100)}%</dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt>AI anomaly score</dt>
                    <dd>{Math.round(selectedAlert.anomaly_score * 100)}%</dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt>Detected</dt>
                    <dd>{formatDateTime(selectedAlert.created_at)}</dd>
                  </div>
                </dl>
              </div>

              <div className="rounded-[1.5rem] border border-brand-black/8 bg-white p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-brand-black">Status update</p>
                    <p className="mt-1 text-xs text-brand-black/55">
                      Analysts and admins can update the current alert workflow state.
                    </p>
                  </div>
                  <StatusBadge variant={selectedAlert.status}>
                    {selectedAlert.status.replace("_", " ")}
                  </StatusBadge>
                </div>

                <div className="mt-4 grid gap-3 sm:grid-cols-[1fr_auto]">
                  <select
                    value={statusDraft}
                    onChange={(event) => setStatusDraft(event.target.value as AlertStatus)}
                    className="input-shell w-full bg-brand-light/50"
                    disabled={!canEditStatus || updateLoading}
                  >
                    {statusOptions
                      .filter((option) => option.value !== "all")
                      .map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                  </select>

                  <button
                    type="button"
                    onClick={handleStatusUpdate}
                    className="btn-primary"
                    disabled={!canEditStatus || updateLoading || statusDraft === selectedAlert.status}
                  >
                    {updateLoading ? "Saving..." : "Update status"}
                  </button>
                </div>

                <p className="mt-3 text-xs text-brand-black/55">
                  {canEditStatus
                    ? "Status changes update the live in-memory backend."
                    : "Viewer accounts can review alerts but cannot change alert status."}
                </p>

                {updateMessage ? (
                  <div className="mt-4 rounded-[1.25rem] border border-brand-orange/15 bg-brand-orange/5 px-4 py-3 text-sm text-brand-black/75">
                    {updateMessage}
                  </div>
                ) : null}
              </div>

              <div className="rounded-[1.5rem] border border-brand-black/8 bg-white p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-brand-black">Response actions</p>
                    <p className="mt-1 text-xs text-brand-black/55">
                      Run lab-safe escalation or containment actions and review the response audit
                      history for this alert.
                    </p>
                  </div>
                  <button type="button" onClick={() => navigate("/incidents")} className="btn-secondary">
                    Open incidents
                  </button>
                </div>

                {responseActionsError ? (
                  <div className="mt-4 rounded-[1.25rem] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    {responseActionsError}
                  </div>
                ) : null}

                {responseActionsLoading && !responseActions ? (
                  <div className="mt-4 h-40 animate-pulse rounded-[1.5rem] bg-brand-light/70" />
                ) : (
                  <div className="mt-4 space-y-5">
                    <div className="grid gap-3">
                      {recommendedActions.length > 0 ? (
                        recommendedActions.map((action) => (
                          <div
                            key={action.action_type}
                            className="rounded-[1.25rem] border border-brand-black/8 bg-brand-light/45 p-4"
                          >
                            <div className="flex flex-wrap items-start justify-between gap-3">
                              <div className="min-w-0 flex-1">
                                <div className="flex flex-wrap items-center gap-2">
                                  <p className="text-sm font-semibold text-brand-black">
                                    {action.label}
                                  </p>
                                  <span
                                    className={`inline-flex items-center rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] ring-1 ring-inset ${
                                      action.automated
                                        ? "bg-sky-100 text-sky-700 ring-sky-200"
                                        : "bg-brand-black/5 text-brand-black/70 ring-brand-black/10"
                                    }`}
                                  >
                                    {action.automated ? "Auto-ready" : "Manual"}
                                  </span>
                                </div>
                                <p className="mt-2 text-sm leading-6 text-brand-black/68">
                                  {action.description}
                                </p>
                                {action.target_label ? (
                                  <p className="mt-2 text-xs font-medium uppercase tracking-[0.16em] text-brand-black/45">
                                    Target: {action.target_label}
                                  </p>
                                ) : null}
                              </div>

                              <button
                                type="button"
                                onClick={() => handleExecuteResponseAction(action.action_type)}
                                className={action.available ? "btn-primary" : "btn-secondary"}
                                disabled={
                                  !canRunResponseActions ||
                                  !action.available ||
                                  responseActionLoading !== null
                                }
                              >
                                {responseActionLoading === action.action_type
                                  ? "Running..."
                                  : action.available
                                    ? "Run action"
                                    : "Already applied"}
                              </button>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="rounded-[1.25rem] border border-dashed border-brand-black/10 bg-brand-light/45 px-4 py-5 text-sm text-brand-black/55">
                          No response actions are available for this alert yet.
                        </div>
                      )}
                    </div>

                    <p className="text-xs text-brand-black/55">
                      {canRunResponseActions
                        ? "Admins and analysts can run these actions. Containment changes are recorded as lab-safe simulated responses only."
                        : "Viewer accounts can review the response plan and audit trail but cannot run response actions."}
                    </p>

                    {responseActionMessage ? (
                      <div className="rounded-[1.25rem] border border-brand-orange/15 bg-brand-orange/5 px-4 py-3 text-sm text-brand-black/75">
                        {responseActionMessage}
                      </div>
                    ) : null}

                    <div className="space-y-3">
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-semibold text-brand-black">Audit history</p>
                        <p className="text-xs uppercase tracking-[0.16em] text-brand-black/40">
                          {responseActionHistory.length} entries
                        </p>
                      </div>

                      {responseActionHistory.length > 0 ? (
                        <div className="space-y-3">
                          {responseActionHistory.map((action) => (
                            <div
                              key={action.id}
                              className="rounded-[1.25rem] border border-brand-black/8 bg-white p-4"
                            >
                              <div className="flex flex-wrap items-center gap-2">
                                <p className="text-sm font-semibold text-brand-black">
                                  {getResponseActionLabel(action.action_type)}
                                </p>
                                <span
                                  className={`inline-flex items-center rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] ring-1 ring-inset ${getResponseModeTone(action.execution_mode)}`}
                                >
                                  {action.execution_mode}
                                </span>
                                <span
                                  className={`inline-flex items-center rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] ring-1 ring-inset ${getResponseActionTone(action)}`}
                                >
                                  {action.status}
                                </span>
                              </div>

                              <p className="mt-3 text-sm leading-6 text-brand-black/70">
                                {action.result_summary}
                              </p>

                              <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2 text-xs uppercase tracking-[0.12em] text-brand-black/42">
                                <span>By {action.performed_by_name}</span>
                                {action.target_label ? <span>Target {action.target_label}</span> : null}
                                <span>{formatDateTime(action.created_at)}</span>
                              </div>

                              {action.notes ? (
                                <p className="mt-3 text-sm text-brand-black/58">{action.notes}</p>
                              ) : null}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="rounded-[1.25rem] border border-dashed border-brand-black/10 bg-brand-light/45 px-4 py-5 text-sm text-brand-black/55">
                          No response actions have been recorded for this alert yet.
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="rounded-[1.5rem] border border-dashed border-brand-black/10 bg-brand-light/50 p-10 text-center text-sm text-brand-black/55">
              Select an alert from the table to inspect its details.
            </div>
          )}
        </SectionCard>
      </div>
    </div>
  );
}
