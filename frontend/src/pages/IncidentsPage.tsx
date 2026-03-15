import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { DataTable, type DataTableColumn } from "@/components/DataTable";
import { SectionCard } from "@/components/SectionCard";
import { SeverityBadge } from "@/components/SeverityBadge";
import { StatusBadge } from "@/components/StatusBadge";
import { useAuth } from "@/hooks/useAuth";
import { fetchIncidentById, fetchIncidents, patchIncident } from "@/services/api";
import type { UserRole } from "@/types/auth";
import type {
  IncidentApiRecord,
  IncidentAssigneeOption,
  IncidentListResponse,
  IncidentStatus,
  SeverityLevel,
} from "@/types/domain";

const priorityOptions: Array<{ value: "all" | SeverityLevel; label: string }> = [
  { value: "all", label: "All priorities" },
  { value: "critical", label: "Critical" },
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
];

const statusOptions: Array<{ value: "all" | IncidentStatus; label: string }> = [
  { value: "all", label: "All statuses" },
  { value: "open", label: "Open" },
  { value: "triaged", label: "Triaged" },
  { value: "in_progress", label: "In progress" },
  { value: "resolved", label: "Resolved" },
];

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

const sourceLabels: Record<NonNullable<IncidentApiRecord["source_tool"]>, string> = {
  wazuh: "Wazuh",
  suricata: "Suricata",
  nmap: "Nmap",
  hydra: "Hydra",
  virtualbox: "VirtualBox",
};

function getSourceLabel(sourceTool: IncidentApiRecord["source_tool"]) {
  if (!sourceTool) {
    return "Linked alert";
  }

  return sourceLabels[sourceTool];
}

function getSourceNote(sourceTool: IncidentApiRecord["source_tool"]) {
  if (sourceTool === "nmap") {
    return "Imported lab assessment results only";
  }

  if (sourceTool === "hydra") {
    return "Imported lab credential assessment results only";
  }

  return null;
}

function getAssignmentStatus(incident: IncidentApiRecord) {
  return incident.assigned_to_user_id ? "assigned" : "unassigned";
}

function canManageIncidents(userRole: UserRole | undefined) {
  return userRole === "admin" || userRole === "analyst";
}

const incidentColumns: DataTableColumn<IncidentApiRecord>[] = [
  {
    key: "title",
    header: "Incident",
    render: (incident) => (
      <div>
        <p className="font-semibold text-brand-black">{incident.title}</p>
        <p className="mt-1 text-xs text-brand-black/55">
          {incident.id} - {incident.affected_asset}
        </p>
      </div>
    ),
  },
  {
    key: "priority",
    header: "Priority",
    render: (incident) => <SeverityBadge level={incident.priority} />,
  },
  {
    key: "assignee",
    header: "Assignee",
    render: (incident) =>
      incident.assigned_to_name ? (
        <div>
          <p className="font-medium text-brand-black">{incident.assigned_to_name}</p>
          <p className="mt-1 text-xs text-brand-black/50">Analyst owner</p>
        </div>
      ) : (
        <StatusBadge variant="unassigned">unassigned</StatusBadge>
      ),
  },
  {
    key: "status",
    header: "Status",
    render: (incident) => (
      <StatusBadge variant={incident.status}>{incident.status.replace("_", " ")}</StatusBadge>
    ),
  },
  {
    key: "opened_at",
    header: "Opened",
    render: (incident) => <span>{formatDateTime(incident.opened_at)}</span>,
  },
];

export function IncidentsPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const queryIncidentId = searchParams.get("incidentId");
  const { token, user } = useAuth();
  const [incidentsResponse, setIncidentsResponse] = useState<IncidentListResponse | null>(null);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(queryIncidentId);
  const [selectedIncident, setSelectedIncident] = useState<IncidentApiRecord | null>(null);
  const [priorityFilter, setPriorityFilter] = useState<"all" | SeverityLevel>("all");
  const [statusFilter, setStatusFilter] = useState<"all" | IncidentStatus>("all");
  const [assigneeFilter, setAssigneeFilter] = useState("all");
  const [listLoading, setListLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [listError, setListError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [assigneeDraft, setAssigneeDraft] = useState("");
  const [priorityDraft, setPriorityDraft] = useState<SeverityLevel>("medium");
  const [statusDraft, setStatusDraft] = useState<IncidentStatus>("open");
  const [notesDraft, setNotesDraft] = useState("");

  useEffect(() => {
    if (queryIncidentId) {
      setSelectedIncidentId(queryIncidentId);
    }
  }, [queryIncidentId]);

  useEffect(() => {
    if (!token) {
      return;
    }

    let isActive = true;
    setListLoading(true);
    setListError(null);

    void fetchIncidents(token, {
      priority: priorityFilter === "all" ? undefined : priorityFilter,
      status: statusFilter === "all" ? undefined : statusFilter,
      assignee_id: assigneeFilter === "all" ? undefined : assigneeFilter,
    })
      .then((response) => {
        if (!isActive) {
          return;
        }

        setIncidentsResponse(response);
        setSelectedIncidentId((currentId) => {
          if (queryIncidentId && response.items.some((incident) => incident.id === queryIncidentId)) {
            return queryIncidentId;
          }

          if (currentId && response.items.some((incident) => incident.id === currentId)) {
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
          requestError instanceof Error
            ? requestError.message
            : "The incident list could not be loaded.",
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
  }, [token, priorityFilter, statusFilter, assigneeFilter, reloadKey, queryIncidentId]);

  useEffect(() => {
    if (!token || !selectedIncidentId) {
      setSelectedIncident(null);
      setDetailError(null);
      return;
    }

    let isActive = true;
    setDetailLoading(true);
    setDetailError(null);

    void fetchIncidentById(token, selectedIncidentId)
      .then((response) => {
        if (!isActive) {
          return;
        }

        setSelectedIncident(response);
        setAssigneeDraft(response.assigned_to_user_id ?? "");
        setPriorityDraft(response.priority);
        setStatusDraft(response.status);
        setNotesDraft(response.notes);
      })
      .catch((requestError: unknown) => {
        if (!isActive) {
          return;
        }

        setDetailError(
          requestError instanceof Error
            ? requestError.message
            : "The incident detail could not be loaded.",
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
  }, [token, selectedIncidentId, reloadKey]);

  const handleRetry = () => {
    setReloadKey((currentValue) => currentValue + 1);
  };

  const handleSave = async () => {
    if (!token || !selectedIncidentId) {
      return;
    }

    setSaveLoading(true);
    setSaveMessage(null);

    try {
      const updatedIncident = await patchIncident(token, selectedIncidentId, {
        assigned_to_user_id: assigneeDraft || null,
        priority: priorityDraft,
        status: statusDraft,
        notes: notesDraft,
      });

      setSelectedIncident(updatedIncident);
      setSaveMessage("Incident workflow updated successfully.");
      setReloadKey((currentValue) => currentValue + 1);
    } catch (requestError) {
      setSaveMessage(
        requestError instanceof Error
          ? requestError.message
          : "The incident could not be updated.",
      );
    } finally {
      setSaveLoading(false);
    }
  };

  const incidents = incidentsResponse?.items ?? [];
  const assignees = incidentsResponse?.available_assignees ?? [];
  const canEdit = canManageIncidents(user?.role);

  const summaryMetrics = useMemo(() => {
    return {
      assigned: incidents.filter((incident) => incident.assigned_to_user_id).length,
      unassigned: incidents.filter((incident) => !incident.assigned_to_user_id).length,
      resolved: incidents.filter((incident) => incident.status === "resolved").length,
      active: incidents.filter((incident) => incident.status !== "resolved").length,
    };
  }, [incidents]);

  return (
    <div className="space-y-6">
      <SectionCard
        title="Incident workflow board"
        description="Manage live cases linked to alert activity, route them to analysts, and keep notes and status updates ready for a clean project presentation."
        eyebrow="Incidents"
        action={
          <button
            type="button"
            onClick={() => navigate("/alerts")}
            className="btn-primary"
          >
            Create from alert
          </button>
        }
      >
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Active cases</p>
            <p className="mt-3 text-2xl font-semibold text-brand-black">{summaryMetrics.active}</p>
            <p className="mt-1 text-sm text-brand-black/60">Open, triaged, or in progress</p>
          </div>
          <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Assigned</p>
            <p className="mt-3 text-2xl font-semibold text-brand-black">{summaryMetrics.assigned}</p>
            <p className="mt-1 text-sm text-brand-black/60">Analyst ownership in place</p>
          </div>
          <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Unassigned</p>
            <p className="mt-3 text-2xl font-semibold text-brand-black">{summaryMetrics.unassigned}</p>
            <p className="mt-1 text-sm text-brand-black/60">Needs routing to an analyst</p>
          </div>
          <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Resolved</p>
            <p className="mt-3 text-2xl font-semibold text-brand-black">{summaryMetrics.resolved}</p>
            <p className="mt-1 text-sm text-brand-black/60">Ready for reporting follow-up</p>
          </div>
        </div>
      </SectionCard>

      <SectionCard
        title="Workflow filters"
        description="Focus the incident queue by priority, status, or analyst ownership."
        action={
          <button type="button" onClick={handleRetry} className="btn-secondary" disabled={listLoading}>
            {listLoading ? "Refreshing..." : "Refresh queue"}
          </button>
        }
      >
        <div className="grid gap-4 lg:grid-cols-3">
          <label className="block text-sm font-medium text-brand-black">
            Priority
            <select
              value={priorityFilter}
              onChange={(event) => setPriorityFilter(event.target.value as "all" | SeverityLevel)}
              className="input-shell mt-2 w-full bg-white"
            >
              {priorityOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-sm font-medium text-brand-black">
            Status
            <select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value as "all" | IncidentStatus)}
              className="input-shell mt-2 w-full bg-white"
            >
              {statusOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-sm font-medium text-brand-black">
            Assignee
            <select
              value={assigneeFilter}
              onChange={(event) => setAssigneeFilter(event.target.value)}
              className="input-shell mt-2 w-full bg-white"
            >
              <option value="all">All assignees</option>
              {assignees.map((assignee) => (
                <option key={assignee.id} value={assignee.id}>
                  {assignee.full_name}
                </option>
              ))}
            </select>
          </label>
        </div>
      </SectionCard>

      <div className="grid gap-6 xl:grid-cols-[1.45fr_0.95fr]">
        <SectionCard
          title="Incidents table"
          description={`${incidentsResponse?.total_items ?? 0} incidents currently match the active workflow filters.`}
        >
          {listError ? (
            <div className="space-y-4">
              <div className="rounded-[1.5rem] border border-red-200 bg-red-50 px-4 py-5 text-sm text-red-700">
                {listError}
              </div>
              <button type="button" onClick={handleRetry} className="btn-primary">
                Retry incidents
              </button>
            </div>
          ) : listLoading && !incidentsResponse ? (
            <div className="h-80 animate-pulse rounded-[1.5rem] bg-brand-light/70" />
          ) : (
            <DataTable
              columns={incidentColumns}
              rows={incidents}
              rowKey={(incident) => incident.id}
              onRowClick={(incident) => setSelectedIncidentId(incident.id)}
              selectedRowKey={selectedIncidentId ?? undefined}
              emptyMessage="No incidents match the current filters."
            />
          )}
        </SectionCard>

        <div className="space-y-6">
          <SectionCard
            title="Incident details"
            description="Review linked alert context, analyst assignment, and case progression."
          >
            {!selectedIncidentId && !listLoading ? (
              <div className="rounded-[1.5rem] border border-dashed border-brand-black/10 bg-brand-light/50 p-10 text-center text-sm text-brand-black/55">
                Select an incident from the table to inspect or edit it.
              </div>
            ) : detailLoading && !selectedIncident ? (
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
            ) : selectedIncident ? (
              <div className="space-y-4">
                <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
                  <p className="text-xs uppercase tracking-[0.24em] text-brand-orange">
                    {selectedIncident.id}
                  </p>
                  <h3 className="mt-2 text-xl font-semibold text-brand-black">
                    {selectedIncident.title}
                  </h3>
                  <p className="mt-3 text-sm leading-6 text-brand-black/70">
                    {selectedIncident.summary}
                  </p>
                </div>

                {getSourceNote(selectedIncident.source_tool) ? (
                  <div className="rounded-[1.5rem] border border-brand-orange/20 bg-brand-orange/5 px-4 py-4 text-sm text-brand-black/70">
                    {getSourceNote(selectedIncident.source_tool)}. This incident is linked to a safe
                    imported classroom artifact rather than an offensive automation workflow.
                  </div>
                ) : null}

                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-[1.5rem] border border-brand-black/8 bg-white p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Priority</p>
                    <div className="mt-3">
                      <SeverityBadge level={selectedIncident.priority} />
                    </div>
                  </div>
                  <div className="rounded-[1.5rem] border border-brand-black/8 bg-white p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Status</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <StatusBadge variant={selectedIncident.status}>
                        {selectedIncident.status.replace("_", " ")}
                      </StatusBadge>
                      <StatusBadge variant={getAssignmentStatus(selectedIncident)}>
                        {getAssignmentStatus(selectedIncident)}
                      </StatusBadge>
                    </div>
                  </div>
                </div>

                <div className="rounded-[1.5rem] border border-brand-black/8 bg-white p-4">
                  <p className="text-sm font-semibold text-brand-black">Linked context</p>
                  <dl className="mt-4 space-y-3 text-sm text-brand-black/70">
                    <div className="flex justify-between gap-4">
                      <dt>Linked alert</dt>
                      <dd>{selectedIncident.alert_title ?? "Manual incident"}</dd>
                    </div>
                    <div className="flex justify-between gap-4">
                      <dt>Source tool</dt>
                      <dd>{getSourceLabel(selectedIncident.source_tool)}</dd>
                    </div>
                    <div className="flex justify-between gap-4">
                      <dt>Affected asset</dt>
                      <dd>{selectedIncident.affected_asset}</dd>
                    </div>
                    <div className="flex justify-between gap-4">
                      <dt>Opened</dt>
                      <dd>{formatDateTime(selectedIncident.opened_at)}</dd>
                    </div>
                    <div className="flex justify-between gap-4">
                      <dt>Last updated</dt>
                      <dd>{formatDateTime(selectedIncident.updated_at)}</dd>
                    </div>
                  </dl>
                </div>
              </div>
            ) : null}
          </SectionCard>

          <SectionCard
            title="Workflow editor"
            description="Update assignment, status, priority, and analyst notes from one control surface."
          >
            {selectedIncident ? (
              <div className="space-y-4">
                <label className="block text-sm font-medium text-brand-black">
                  Assigned analyst
                  <select
                    value={assigneeDraft}
                    onChange={(event) => setAssigneeDraft(event.target.value)}
                    className="input-shell mt-2 w-full bg-white"
                    disabled={!canEdit || saveLoading}
                  >
                    <option value="">Unassigned</option>
                    {assignees.map((assignee: IncidentAssigneeOption) => (
                      <option key={assignee.id} value={assignee.id}>
                        {assignee.full_name}
                      </option>
                    ))}
                  </select>
                </label>

                <div className="grid gap-3 sm:grid-cols-2">
                  <label className="block text-sm font-medium text-brand-black">
                    Priority
                    <select
                      value={priorityDraft}
                      onChange={(event) => setPriorityDraft(event.target.value as SeverityLevel)}
                      className="input-shell mt-2 w-full bg-white"
                      disabled={!canEdit || saveLoading}
                    >
                      {priorityOptions
                        .filter((option) => option.value !== "all")
                        .map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                    </select>
                  </label>

                  <label className="block text-sm font-medium text-brand-black">
                    Status
                    <select
                      value={statusDraft}
                      onChange={(event) => setStatusDraft(event.target.value as IncidentStatus)}
                      className="input-shell mt-2 w-full bg-white"
                      disabled={!canEdit || saveLoading}
                    >
                      {statusOptions
                        .filter((option) => option.value !== "all")
                        .map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                    </select>
                  </label>
                </div>

                <label className="block text-sm font-medium text-brand-black">
                  Analyst notes
                  <textarea
                    rows={6}
                    value={notesDraft}
                    onChange={(event) => setNotesDraft(event.target.value)}
                    className="input-shell mt-2 w-full resize-none bg-white text-sm text-brand-black outline-none placeholder:text-brand-black/40"
                    placeholder="Capture triage notes, analyst reasoning, or remediation progress."
                    disabled={!canEdit || saveLoading}
                  />
                </label>

                <p className="text-xs text-brand-black/55">
                  {canEdit
                    ? "Analysts and admins can update the in-memory demo workflow for live presentations."
                    : "Viewer accounts can inspect incidents but cannot edit assignment, notes, or status."}
                </p>

                <div className="flex flex-col gap-3 sm:flex-row">
                  <button
                    type="button"
                    onClick={handleSave}
                    className="btn-primary"
                    disabled={!canEdit || saveLoading}
                  >
                    {saveLoading ? "Saving changes..." : "Save incident updates"}
                  </button>
                  <button
                    type="button"
                    onClick={() => navigate("/alerts")}
                    className="btn-secondary"
                  >
                    Open alerts queue
                  </button>
                </div>

                {saveMessage ? (
                  <div className="rounded-[1.25rem] border border-brand-orange/15 bg-brand-orange/5 px-4 py-3 text-sm text-brand-black/75">
                    {saveMessage}
                  </div>
                ) : null}
              </div>
            ) : (
              <div className="rounded-[1.5rem] border border-dashed border-brand-black/10 bg-brand-light/50 p-10 text-center text-sm text-brand-black/55">
                Select an incident to update its workflow.
              </div>
            )}
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
