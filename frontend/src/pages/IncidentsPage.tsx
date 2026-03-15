import { DataTable, type DataTableColumn } from "@/components/DataTable";
import { SectionCard } from "@/components/SectionCard";
import { SeverityBadge } from "@/components/SeverityBadge";
import { StatusBadge } from "@/components/StatusBadge";
import { incidents } from "@/data/mock";
import type { IncidentRecord } from "@/types/domain";

const incidentColumns: DataTableColumn<IncidentRecord>[] = [
  {
    key: "title",
    header: "Incident",
    render: (incident) => (
      <div>
        <p className="font-semibold text-brand-black">{incident.title}</p>
        <p className="mt-1 text-xs text-brand-black/55">
          {incident.id} - {incident.affectedAsset}
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
    key: "assignmentStatus",
    header: "Assignment",
    render: (incident) => (
      <StatusBadge variant={incident.assignmentStatus}>{incident.assignmentStatus}</StatusBadge>
    ),
  },
  {
    key: "analyst",
    header: "Analyst",
    render: (incident) => <span>{incident.analyst}</span>,
  },
  {
    key: "status",
    header: "Status",
    render: (incident) => (
      <StatusBadge variant={incident.status}>{incident.status.replace("_", " ")}</StatusBadge>
    ),
  },
];

export function IncidentsPage() {
  const highlightedIncident = incidents[0];

  return (
    <div className="space-y-6">
      <SectionCard
        title="Incident workflow board"
        description="Track analyst ownership, assignment posture, and status updates with a clean case-management presentation layout."
        eyebrow="Incidents"
        action={<button className="btn-primary">Create incident</button>}
      >
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Assigned</p>
            <p className="mt-3 text-2xl font-semibold text-brand-black">07</p>
            <p className="mt-1 text-sm text-brand-black/60">Active analyst ownership</p>
          </div>
          <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Escalated</p>
            <p className="mt-3 text-2xl font-semibold text-brand-black">03</p>
            <p className="mt-1 text-sm text-brand-black/60">Requires admin review</p>
          </div>
          <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Avg. response</p>
            <p className="mt-3 text-2xl font-semibold text-brand-black">18m</p>
            <p className="mt-1 text-sm text-brand-black/60">Triage-to-assignment placeholder</p>
          </div>
        </div>
      </SectionCard>

      <div className="grid gap-6 xl:grid-cols-[1.45fr_0.95fr]">
        <SectionCard title="Incidents table" description="Current case list and assignment posture.">
          <DataTable columns={incidentColumns} rows={incidents} rowKey={(incident) => incident.id} />
        </SectionCard>

        <div className="space-y-6">
          <SectionCard
            title="Analyst assignment"
            description="Placeholder controls for routing the selected case."
            action={<button className="btn-secondary">Edit routing</button>}
          >
            <div className="space-y-4">
              <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Selected case</p>
                <p className="mt-2 text-lg font-semibold text-brand-black">
                  {highlightedIncident.title}
                </p>
                <p className="mt-2 text-sm text-brand-black/60">{highlightedIncident.summary}</p>
              </div>

              <div className="grid gap-3">
                <label className="block text-sm font-medium text-brand-black">
                  Assigned analyst
                  <select className="input-shell mt-2 w-full bg-white">
                    <option>A. Silva</option>
                    <option>M. Perera</option>
                    <option>Admin Review</option>
                  </select>
                </label>
                <label className="block text-sm font-medium text-brand-black">
                  Priority
                  <select className="input-shell mt-2 w-full bg-white">
                    <option>Critical</option>
                    <option>High</option>
                    <option>Medium</option>
                    <option>Low</option>
                  </select>
                </label>
              </div>

              <button className="btn-primary w-full">Save assignment placeholder</button>
            </div>
          </SectionCard>

          <SectionCard
            title="Status update"
            description="Simple placeholder controls for case progression."
          >
            <div className="space-y-4">
              <div className="flex flex-wrap gap-2">
                <StatusBadge variant={highlightedIncident.status}>
                  {highlightedIncident.status.replace("_", " ")}
                </StatusBadge>
                <StatusBadge variant={highlightedIncident.assignmentStatus}>
                  {highlightedIncident.assignmentStatus}
                </StatusBadge>
              </div>
              <textarea
                rows={5}
                placeholder="Add a timeline note, analyst summary, or remediation update"
                className="input-shell w-full resize-none bg-white text-sm text-brand-black outline-none placeholder:text-brand-black/40"
              />
              <div className="grid gap-3 sm:grid-cols-2">
                <button className="btn-secondary">Set to triaged</button>
                <button className="btn-primary">Mark in progress</button>
              </div>
            </div>
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
