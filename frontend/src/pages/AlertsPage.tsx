import { useEffect, useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/DataTable";
import { FilterIcon, SearchIcon } from "@/components/Icons";
import { SectionCard } from "@/components/SectionCard";
import { SeverityBadge } from "@/components/SeverityBadge";
import { StatusBadge } from "@/components/StatusBadge";
import { alerts } from "@/data/mock";
import type { AlertRecord, AlertStatus, SeverityLevel } from "@/types/domain";

const alertColumns: DataTableColumn<AlertRecord>[] = [
  {
    key: "title",
    header: "Alert",
    render: (alert) => (
      <div>
        <p className="font-semibold text-brand-black">{alert.title}</p>
        <p className="mt-1 text-xs text-brand-black/55">
          {alert.source} - {alert.asset}
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
    key: "status",
    header: "Status",
    render: (alert) => <StatusBadge variant={alert.status}>{alert.status.replace("_", " ")}</StatusBadge>,
  },
  {
    key: "analyst",
    header: "Analyst",
    render: (alert) => <span>{alert.analyst}</span>,
  },
  {
    key: "createdAt",
    header: "Detected",
    render: (alert) => <span>{alert.createdAt}</span>,
  },
];

const severityOptions: Array<"all" | SeverityLevel> = ["all", "critical", "high", "medium", "low"];
const statusOptions: Array<"all" | AlertStatus> = ["all", "new", "triaged", "investigating", "resolved"];

export function AlertsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [severityFilter, setSeverityFilter] = useState<"all" | SeverityLevel>("all");
  const [statusFilter, setStatusFilter] = useState<"all" | AlertStatus>("all");
  const [selectedAlertId, setSelectedAlertId] = useState(alerts[0]?.id ?? "");

  const filteredAlerts = alerts.filter((alert) => {
    const query = searchQuery.trim().toLowerCase();
    const matchesQuery =
      query.length === 0 ||
      alert.title.toLowerCase().includes(query) ||
      alert.source.toLowerCase().includes(query) ||
      alert.asset.toLowerCase().includes(query);

    const matchesSeverity = severityFilter === "all" || alert.severity === severityFilter;
    const matchesStatus = statusFilter === "all" || alert.status === statusFilter;

    return matchesQuery && matchesSeverity && matchesStatus;
  });

  useEffect(() => {
    if (!filteredAlerts.find((alert) => alert.id === selectedAlertId)) {
      setSelectedAlertId(filteredAlerts[0]?.id ?? "");
    }
  }, [filteredAlerts, selectedAlertId]);

  const selectedAlert = filteredAlerts.find((alert) => alert.id === selectedAlertId) ?? filteredAlerts[0];

  return (
    <div className="space-y-6">
      <SectionCard
        title="Alert investigation workspace"
        description="Search, filter, and review high-signal events with a clear detail panel for presentation walkthroughs."
        eyebrow="Alerts"
        action={<button className="btn-primary">Create watchlist</button>}
      >
        <div className="grid gap-4 lg:grid-cols-[1.2fr_0.9fr_0.9fr]">
          <label className="input-shell flex items-center gap-3">
            <SearchIcon className="h-4 w-4 text-brand-black/45" />
            <input
              type="text"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search title, source, or asset"
              className="w-full bg-transparent text-sm text-brand-black outline-none placeholder:text-brand-black/40"
            />
          </label>

          <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-brand-black">
              <FilterIcon className="h-4 w-4" />
              Severity
            </div>
            <div className="flex flex-wrap gap-2">
              {severityOptions.map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => setSeverityFilter(option)}
                  className={`rounded-full px-3 py-1 text-xs font-semibold capitalize ${severityFilter === option ? "bg-brand-orange text-white" : "bg-white text-brand-black/70"}`}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>

          <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-brand-black">
              <FilterIcon className="h-4 w-4" />
              Status
            </div>
            <div className="flex flex-wrap gap-2">
              {statusOptions.map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => setStatusFilter(option)}
                  className={`rounded-full px-3 py-1 text-xs font-semibold capitalize ${statusFilter === option ? "bg-brand-orange text-white" : "bg-white text-brand-black/70"}`}
                >
                  {option.replace("_", " ")}
                </button>
              ))}
            </div>
          </div>
        </div>
      </SectionCard>

      <div className="grid gap-6 xl:grid-cols-[1.45fr_0.95fr]">
        <SectionCard
          title="Alert queue"
          description={`${filteredAlerts.length} alerts currently match the selected filters.`}
        >
          <DataTable
            columns={alertColumns}
            rows={filteredAlerts}
            rowKey={(alert) => alert.id}
            compact
            onRowClick={(alert) => setSelectedAlertId(alert.id)}
            selectedRowKey={selectedAlertId}
          />
        </SectionCard>

        <SectionCard
          title="Alert details"
          description="Focused context for the currently selected alert."
          action={<button className="btn-secondary">Escalate placeholder</button>}
        >
          {selectedAlert ? (
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
                <p className="text-sm font-semibold text-brand-black">Context</p>
                <dl className="mt-4 space-y-3 text-sm text-brand-black/70">
                  <div className="flex justify-between gap-4">
                    <dt>Source</dt>
                    <dd>{selectedAlert.source}</dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt>Asset</dt>
                    <dd>{selectedAlert.asset}</dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt>Analyst</dt>
                    <dd>{selectedAlert.analyst}</dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt>Detected</dt>
                    <dd>{selectedAlert.createdAt}</dd>
                  </div>
                </dl>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <button className="btn-primary">Assign analyst</button>
                <button className="btn-secondary">Mark as triaged</button>
              </div>
            </div>
          ) : (
            <div className="rounded-[1.5rem] border border-dashed border-brand-black/10 bg-brand-light/50 p-10 text-center text-sm text-brand-black/55">
              No alert matches the current filters.
            </div>
          )}
        </SectionCard>
      </div>
    </div>
  );
}
