import { ContentCard } from "@/components/ContentCard";
import { DataTable } from "@/components/DataTable";
import { PageHeader } from "@/components/PageHeader";
import { StatusBadge } from "@/components/StatusBadge";
import { integrationRows } from "@/data/mock";

const columns = [
  { key: "id", label: "Integration ID" },
  { key: "name", label: "Integration" },
  { key: "mode", label: "Mode" },
  { key: "status", label: "Status" },
  { key: "lastSync", label: "Last sync" }
];

export function IntegrationsPage() {
  const rows = integrationRows.map((integration) => ({
    ...integration,
    status: (
      <StatusBadge variant={integration.status as "connected" | "pending"}>
        {integration.status}
      </StatusBadge>
    )
  }));

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Data sources"
        title="Integrations"
        description="Starter integration scaffolding for Wazuh, Suricata, and safe lab-only Nmap/Hydra file ingestion."
        action={<button className="btn-primary">Add source</button>}
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <ContentCard
          title="Ingestion strategy"
          description="Keep source adapters isolated from API handlers and validate all imported files before processing."
        >
          <ul className="space-y-3 text-sm text-brand-black/70">
            <li>Wazuh and Suricata should be first-class ingestion paths.</li>
            <li>Nmap and Hydra support must remain lab-only and non-executing.</li>
            <li>Normalize records before surfacing them to charts and dashboards.</li>
          </ul>
        </ContentCard>

        <ContentCard
          title="WebSocket readiness"
          description="Backend scaffolding already includes a placeholder socket module for dashboard updates."
        >
          <div className="rounded-[1.25rem] bg-brand-light p-4 text-sm text-brand-black/70">
            Recommended next step: stream alert summaries, ingestion status, and lightweight analyst
            notifications to the dashboard shell.
          </div>
        </ContentCard>
      </div>

      <DataTable columns={columns} rows={rows} />
    </div>
  );
}
