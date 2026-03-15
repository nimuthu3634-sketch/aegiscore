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
import {
  alerts,
  alertsBySeverity,
  alertsOverTime,
  dashboardStats,
  incidents,
} from "@/data/mock";
import type { AlertRecord } from "@/types/domain";

const statIcons = [
  <ShieldIcon key="shield" className="h-5 w-5" />,
  <AlertTriangleIcon key="alert" className="h-5 w-5" />,
  <IncidentIcon key="incident" className="h-5 w-5" />,
  <ReportIcon key="report" className="h-5 w-5" />,
];

const alertColumns: DataTableColumn<AlertRecord>[] = [
  {
    key: "title",
    header: "Alert",
    render: (alert) => (
      <div>
        <p className="font-semibold text-brand-black">{alert.title}</p>
        <p className="mt-1 text-xs text-brand-black/50">
          {alert.source} on {alert.asset}
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

export function DashboardPage() {
  return (
    <div className="space-y-6">
      <SectionCard
        title="Command overview"
        description="A polished lab SOC surface for briefing analysts, tracking current risk, and presenting security activity in a professional format."
        eyebrow="Dashboard"
        tone="dark"
        action={
          <button className="btn-primary inline-flex items-center gap-2">
            Generate briefing
            <ArrowUpRightIcon className="h-4 w-4" />
          </button>
        }
      >
        <div className="grid gap-4 lg:grid-cols-[1.25fr_0.75fr]">
          <div className="rounded-[1.5rem] border border-brand-white/10 bg-brand-white/5 p-5">
            <p className="text-sm font-semibold text-white">Presentation focus</p>
            <p className="mt-2 text-sm leading-6 text-brand-muted">
              Highlight alert volume, incident posture, and integration coverage while keeping all
              workflows limited to safe, lab-only defensive monitoring.
            </p>
          </div>
          <div className="rounded-[1.5rem] border border-brand-white/10 bg-brand-white/5 p-5">
            <p className="text-sm font-semibold text-white">Current emphasis</p>
            <ul className="mt-3 space-y-2 text-sm text-brand-muted">
              <li>Critical alerts need rapid analyst review</li>
              <li>Incident assignment remains visible for presentations</li>
              <li>Wazuh and Suricata remain primary signal sources</li>
            </ul>
          </div>
        </div>
      </SectionCard>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {dashboardStats.map((stat, index) => (
          <StatCard
            key={stat.label}
            label={stat.label}
            value={stat.value}
            change={stat.change}
            helper={stat.helper}
            tone={stat.tone}
            icon={statIcons[index]}
          />
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
        <ChartCard
          title="Alerts over time"
          description="Daily alert volume across the current presentation week."
          data={alertsOverTime.map((point) => ({ name: point.label, total: point.total }))}
          xKey="name"
          yKey="total"
        />

        <ChartCard
          title="Alerts by severity"
          description="Current distribution of alert priorities."
          data={alertsBySeverity.map((point) => ({ label: point.severity, count: point.count }))}
          xKey="label"
          yKey="count"
          variant="bar"
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.45fr_0.95fr]">
        <SectionCard
          title="Recent alerts"
          description="Most recent signals entering the dashboard queue."
          action={<button className="btn-secondary">View all alerts</button>}
        >
          <DataTable columns={alertColumns} rows={alerts.slice(0, 5)} rowKey={(alert) => alert.id} />
        </SectionCard>

        <SectionCard
          title="Recent incidents"
          description="Open case activity that analysts can speak to during demos."
        >
          <div className="space-y-4">
            {incidents.slice(0, 3).map((incident) => (
              <div
                key={incident.id}
                className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-brand-black">{incident.title}</p>
                    <p className="mt-1 text-xs text-brand-black/55">
                      {incident.id} - {incident.affectedAsset}
                    </p>
                  </div>
                  <SeverityBadge level={incident.priority} />
                </div>
                <p className="mt-3 text-sm leading-6 text-brand-black/70">{incident.summary}</p>
                <div className="mt-4 flex flex-wrap items-center gap-2">
                  <StatusBadge variant={incident.status}>{incident.status.replace("_", " ")}</StatusBadge>
                  <StatusBadge variant={incident.assignmentStatus}>
                    {incident.assignmentStatus}
                  </StatusBadge>
                </div>
                <p className="mt-3 text-xs text-brand-black/50">
                  Analyst: {incident.analyst} - Updated {incident.updatedAt}
                </p>
              </div>
            ))}
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
