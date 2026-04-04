"use client";

import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery } from "@tanstack/react-query";
import { Download, FileDown, FileText, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { EmptyState } from "@/components/feedback/empty-state";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { FormField } from "@/components/forms/form-field";
import { PageHeader } from "@/components/shared/page-header";
import { StatCard } from "@/components/shared/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { api, createQueryString, downloadTextFile } from "@/lib/api";
import { formatDate, formatNumber } from "@/lib/format";
import type { DashboardSummary, Incident, PageResult } from "@/types/domain";

const incidentExportSchema = z.object({
  incident_id: z.string().min(1, "Choose an incident to export."),
});

export default function ReportsPage() {
  const [downloading, setDownloading] = useState<string | null>(null);

  const summaryQuery = useQuery({
    queryKey: ["dashboard", "summary", "reports"],
    queryFn: () => api.get<DashboardSummary>("/dashboard/summary"),
  });
  const incidentsQuery = useQuery({
    queryKey: ["reports", "incidents"],
    queryFn: () => api.get<PageResult<Incident>>(`/incidents${createQueryString({ page: 1, page_size: 24 })}`),
  });

  const form = useForm<z.infer<typeof incidentExportSchema>>({
    resolver: zodResolver(incidentExportSchema),
    defaultValues: { incident_id: "" },
  });

  useEffect(() => {
    if (incidentsQuery.data?.items.length && !form.getValues("incident_id")) {
      form.reset({ incident_id: incidentsQuery.data.items[0].id });
    }
  }, [form, incidentsQuery.data]);

  async function handleDownload(key: string, filename: string, path: string, type: string) {
    setDownloading(key);
    try {
      const content = await api.get<string>(path);
      downloadTextFile(filename, content, type);
    } finally {
      setDownloading(null);
    }
  }

  if (summaryQuery.isLoading || incidentsQuery.isLoading) {
    return <LoadingState lines={7} />;
  }

  if (summaryQuery.isError || incidentsQuery.isError || !summaryQuery.data || !incidentsQuery.data) {
    return (
      <ErrorState
        description="Reporting data could not be loaded from the connected APIs."
        onRetry={() => {
          summaryQuery.refetch();
          incidentsQuery.refetch();
        }}
      />
    );
  }

  const incidents = incidentsQuery.data.items;
  const selectedIncidentId = form.watch("incident_id");

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Export center"
        title="Reports"
        description="Generate CSV exports and printable incident summaries for analyst handoff, shift reports, and operational review."
        actions={<Badge tone="medium">CSV and printable text exports</Badge>}
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Open alerts" value={formatNumber(summaryQuery.data.kpis.open_alerts)} detail="Included in alert export coverage" tone="high" />
        <StatCard label="Open incidents" value={formatNumber(summaryQuery.data.kpis.open_incidents)} detail="Available for printable case summaries" tone="medium" />
        <StatCard label="Tracked assets" value={formatNumber(summaryQuery.data.kpis.total_assets)} detail="Reflected in dashboard summary exports" />
        <StatCard label="Exports ready" value="3" detail="Alerts CSV, dashboard CSV, incident summary" tone="healthy" />
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
        <Card>
          <CardHeader>
            <CardTitle>Standard exports</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-[1.25rem] border bg-[#fcfcfc] p-4 text-sm leading-6 text-[#5f5f5f]">
              Use these exports for operational reviews, shift handoffs, or evidence packs. Data is pulled from the live API at download time so exports reflect the current SOC state.
            </div>

            <div className="grid gap-3">
              <button
                type="button"
                className="rounded-[1.25rem] border bg-white p-4 text-left transition hover:border-[#FF7A1A]"
                onClick={() => handleDownload("alerts", "aegiscore-alerts.csv", "/reports/alerts.csv", "text/csv")}
                disabled={downloading !== null}
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-semibold text-[#111111]">Alerts export</p>
                    <p className="mt-1 text-sm text-[#6f6f6f]">Severity, source, risk score, asset mapping, and detection timestamps.</p>
                  </div>
                  <Badge tone="high">CSV</Badge>
                </div>
              </button>

              <button
                type="button"
                className="rounded-[1.25rem] border bg-white p-4 text-left transition hover:border-[#FF7A1A]"
                onClick={() => handleDownload("dashboard", "aegiscore-dashboard.csv", "/reports/dashboard.csv", "text/csv")}
                disabled={downloading !== null}
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-semibold text-[#111111]">Dashboard summary</p>
                    <p className="mt-1 text-sm text-[#6f6f6f]">High-level KPI snapshot of assets, alerts, incidents, and ingestion throughput.</p>
                  </div>
                  <Badge tone="medium">CSV</Badge>
                </div>
              </button>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button
                type="button"
                onClick={() => handleDownload("alerts", "aegiscore-alerts.csv", "/reports/alerts.csv", "text/csv")}
                disabled={downloading !== null}
              >
                <Download className="mr-2 h-4 w-4" />
                {downloading === "alerts" ? "Preparing alerts export..." : "Download alerts CSV"}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => handleDownload("dashboard", "aegiscore-dashboard.csv", "/reports/dashboard.csv", "text/csv")}
                disabled={downloading !== null}
              >
                <FileDown className="mr-2 h-4 w-4" />
                {downloading === "dashboard" ? "Preparing dashboard export..." : "Download dashboard CSV"}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Printable incident summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <form
              className="space-y-4"
              onSubmit={form.handleSubmit(async (values) => {
                await handleDownload(
                  `incident-${values.incident_id}`,
                  `incident-${values.incident_id}.txt`,
                  `/reports/incidents/${values.incident_id}/summary`,
                  "text/plain",
                );
              })}
            >
              <FormField label="Choose incident" error={form.formState.errors.incident_id?.message}>
                <Select {...form.register("incident_id")}>
                  <option value="">Select an incident</option>
                  {incidents.map((incident) => (
                    <option key={incident.id} value={incident.id}>
                      {incident.reference} | {incident.title}
                    </option>
                  ))}
                </Select>
              </FormField>

              <div className="rounded-[1.25rem] border bg-[#fcfcfc] p-4 text-sm leading-6 text-[#5f5f5f]">
                Exported summaries include the incident title, status, priority, opened timestamp, linked alerts, and timeline history in a clean printable text format.
              </div>

              <Button type="submit" disabled={!selectedIncidentId || downloading !== null}>
                <FileText className="mr-2 h-4 w-4" />
                {downloading?.startsWith("incident-") ? "Preparing summary..." : "Download incident summary"}
              </Button>
            </form>

            <div className="space-y-3">
              <p className="text-sm font-semibold text-[#111111]">Recent export-ready cases</p>
              {incidents.length ? (
                incidents.slice(0, 5).map((incident) => (
                  <div key={incident.id} className="flex items-center justify-between gap-3 rounded-[1.25rem] border bg-white px-4 py-4">
                    <div>
                      <Link href={`/incidents/${incident.id}`} className="font-semibold text-[#111111] hover:text-[#FF7A1A]">
                        {incident.reference}
                      </Link>
                      <p className="mt-1 text-sm text-[#6f6f6f]">{incident.title}</p>
                      <p className="mt-2 text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Opened {formatDate(incident.opened_at)}</p>
                    </div>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() =>
                        handleDownload(
                          `incident-${incident.id}`,
                          `${incident.reference.toLowerCase()}.txt`,
                          `/reports/incidents/${incident.id}/summary`,
                          "text/plain",
                        )
                      }
                      disabled={downloading !== null}
                    >
                      Export
                    </Button>
                  </div>
                ))
              ) : (
                <EmptyState
                  title="No incidents available"
                  description="Once incidents are created, export-ready case summaries will appear here for quick download."
                />
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Export guidance</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 lg:grid-cols-3">
          <div className="rounded-[1.25rem] border bg-white p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-[#fff4eb] p-3 text-[#FF7A1A]">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <p className="font-semibold text-[#111111]">Analyst handoff</p>
            </div>
            <p className="mt-4 text-sm leading-6 text-[#6f6f6f]">Use incident summaries when handing a case between lab analysts or presenting containment progress.</p>
          </div>
          <div className="rounded-[1.25rem] border bg-white p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-[#fff4eb] p-3 text-[#FF7A1A]">
                <FileDown className="h-5 w-5" />
              </div>
              <p className="font-semibold text-[#111111]">Operational review</p>
            </div>
            <p className="mt-4 text-sm leading-6 text-[#6f6f6f]">Dashboard CSV exports provide a fast way to review KPI movement and ingestion activity across shifts.</p>
          </div>
          <div className="rounded-[1.25rem] border bg-white p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-[#fff4eb] p-3 text-[#FF7A1A]">
                <Download className="h-5 w-5" />
              </div>
              <p className="font-semibold text-[#111111]">Evidence pack</p>
            </div>
            <p className="mt-4 text-sm leading-6 text-[#6f6f6f]">Alert CSV exports capture the fields most useful for triage evidence and post-lab reporting.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
