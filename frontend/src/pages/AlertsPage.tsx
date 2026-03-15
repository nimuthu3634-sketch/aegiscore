import { DataTable } from "@/components/DataTable";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { StatusBadge } from "@/components/StatusBadge";
import { alertRows } from "@/data/mock";

const columns = [
  { key: "id", label: "Alert ID" },
  { key: "title", label: "Alert" },
  { key: "severity", label: "Severity" },
  { key: "status", label: "Status" },
  { key: "source", label: "Source" },
  { key: "time", label: "Detected" }
];

export function AlertsPage() {
  const rows = alertRows.map((alert) => ({
    ...alert,
    severity: (
      <StatusBadge variant={alert.severity as "critical" | "high" | "medium" | "low"}>
        {alert.severity}
      </StatusBadge>
    ),
    status: (
      <StatusBadge variant={alert.status as "new" | "triaged" | "resolved" | "in_progress"}>
        {alert.status.replace("_", " ")}
      </StatusBadge>
    )
  }));

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Alert queue"
        title="Alerts"
        description="Starter alert triage views for Wazuh, Suricata, and safe lab-result imports."
        action={<button className="btn-primary">Create filter</button>}
      />

      <div className="grid gap-4 md:grid-cols-3">
        <StatCard label="Critical" value="4" change="Needs review" />
        <StatCard label="Unassigned" value="19" change="Triage backlog" />
        <StatCard label="Mean triage time" value="11m" change="Within target" />
      </div>

      <DataTable columns={columns} rows={rows} />
    </div>
  );
}
