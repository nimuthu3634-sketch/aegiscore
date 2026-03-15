import { ChartCard } from "@/components/ChartCard";
import { DataTable, type DataTableColumn } from "@/components/DataTable";
import { DownloadIcon, ReportIcon } from "@/components/Icons";
import { SectionCard } from "@/components/SectionCard";
import { StatCard } from "@/components/StatCard";
import { StatusBadge } from "@/components/StatusBadge";
import { reportCategories, reportMetrics, reports, reportTrend } from "@/data/mock";
import type { ReportRecord } from "@/types/domain";

const reportColumns: DataTableColumn<ReportRecord>[] = [
  {
    key: "name",
    header: "Report",
    render: (report) => (
      <div>
        <p className="font-semibold text-brand-black">{report.name}</p>
        <p className="mt-1 text-xs text-brand-black/55">{report.range}</p>
      </div>
    ),
  },
  {
    key: "owner",
    header: "Owner",
    render: (report) => <span>{report.owner}</span>,
  },
  {
    key: "status",
    header: "Status",
    render: (report) => <StatusBadge variant={report.status}>{report.status}</StatusBadge>,
  },
  {
    key: "generatedAt",
    header: "Generated",
    render: (report) => <span>{report.generatedAt}</span>,
  },
];

export function ReportsPage() {
  return (
    <div className="space-y-6">
      <SectionCard
        title="Reporting workspace"
        description="Presentation-focused reporting views for weekly SOC snapshots, anomaly summaries, and export-ready executive material."
        eyebrow="Reports"
        action={
          <button className="btn-primary inline-flex items-center gap-2">
            <DownloadIcon className="h-4 w-4" />
            Export placeholder
          </button>
        }
      >
        <div className="grid gap-4 md:grid-cols-3">
          <label className="block text-sm font-medium text-brand-black">
            Start date
            <input type="date" className="input-shell mt-2 w-full bg-white" defaultValue="2026-03-01" />
          </label>
          <label className="block text-sm font-medium text-brand-black">
            End date
            <input type="date" className="input-shell mt-2 w-full bg-white" defaultValue="2026-03-15" />
          </label>
          <div className="flex items-end">
            <button className="btn-secondary w-full">Apply range placeholder</button>
          </div>
        </div>
      </SectionCard>

      <div className="grid gap-4 md:grid-cols-3">
        {reportMetrics.map((metric) => (
          <StatCard
            key={metric.label}
            label={metric.label}
            value={metric.value}
            change={metric.detail}
            helper="Report summary metric"
            tone="orange"
            icon={<ReportIcon className="h-5 w-5" />}
          />
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.35fr_1fr]">
        <ChartCard
          title="Incident volume across reporting windows"
          description="Placeholder trend that can later map directly to filtered backend reporting endpoints."
          data={reportTrend.map((item) => ({ label: item.label, incidents: item.incidents }))}
          xKey="label"
          yKey="incidents"
        />

        <ChartCard
          title="Report category distribution"
          description="How current report content is weighted across operational themes."
          data={reportCategories.map((item) => ({ label: item.label, value: item.value }))}
          xKey="label"
          yKey="value"
          variant="bar"
        />
      </div>

      <SectionCard title="Recent exports" description="Scaffolded report output list for demo-ready handoff views.">
        <DataTable columns={reportColumns} rows={reports} rowKey={(report) => report.id} />
      </SectionCard>
    </div>
  );
}
