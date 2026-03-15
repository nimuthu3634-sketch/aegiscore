import { DataTable } from "@/components/DataTable";
import { PageHeader } from "@/components/PageHeader";
import { StatusBadge } from "@/components/StatusBadge";
import { incidentRows } from "@/data/mock";

const columns = [
  { key: "id", label: "Incident ID" },
  { key: "title", label: "Title" },
  { key: "priority", label: "Priority" },
  { key: "owner", label: "Owner" },
  { key: "status", label: "Status" },
  { key: "updated", label: "Last update" }
];

export function IncidentsPage() {
  const rows = incidentRows.map((incident) => ({
    ...incident,
    priority: (
      <StatusBadge variant={incident.priority as "high" | "medium" | "low"}>
        {incident.priority}
      </StatusBadge>
    ),
    status: (
      <StatusBadge variant={incident.status as "triaged" | "resolved" | "in_progress"}>
        {incident.status.replace("_", " ")}
      </StatusBadge>
    )
  }));

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Case management"
        title="Incidents"
        description="Placeholder incident workflow scaffolding for escalation, assignment, and case tracking."
        action={<button className="btn-primary">Open incident</button>}
      />

      <DataTable columns={columns} rows={rows} />
    </div>
  );
}
