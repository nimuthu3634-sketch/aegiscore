"use client";

import Link from "next/link";
import { type ColumnDef } from "@tanstack/react-table";
import { useQuery } from "@tanstack/react-query";
import { useDeferredValue, useState } from "react";

import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { DataTable } from "@/components/tables/data-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { PageHeader } from "@/components/shared/page-header";
import { PaginationControls } from "@/components/shared/pagination-controls";
import { api, createQueryString } from "@/lib/api";
import { formatDate, scoreTone, truncate } from "@/lib/format";
import type { Alert, PageResult } from "@/types/domain";

function ExplainabilityPopover({ alert }: { alert: Alert }) {
  return (
    <details className="group relative">
      <summary className="cursor-pointer list-none text-xs font-medium text-[#FF7A1A]">Why this score?</summary>
      <div className="absolute right-0 z-20 mt-3 w-80 rounded-[1.25rem] border bg-white p-4 shadow-[0_18px_40px_rgba(17,17,17,0.1)]">
        <p className="text-sm font-semibold text-[#111111]">{alert.explanation_summary ?? "Explainability factors"}</p>
        <div className="mt-3 space-y-2">
          {alert.explainability.length ? (
            alert.explainability.map((item) => (
              <div key={item.factor} className="rounded-xl border bg-[#fafafa] px-3 py-2">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm font-medium capitalize">{item.factor}</span>
                  <span className="text-xs text-[#6f6f6f]">Impact {item.impact}</span>
                </div>
              </div>
            ))
          ) : (
            <p className="text-sm text-[#6f6f6f]">No explainability factors were returned for this alert.</p>
          )}
        </div>
      </div>
    </details>
  );
}

const columns: ColumnDef<Alert>[] = [
  {
    accessorKey: "title",
    header: "Alert",
    cell: ({ row }) => {
      const alert = row.original;
      return (
        <div className="space-y-1.5">
          <Link href={`/alerts/${alert.id}`} className="font-semibold text-[#111111] hover:text-[#FF7A1A]">
            {alert.title}
          </Link>
          <p className="max-w-[340px] text-sm leading-6 text-[#6f6f6f]">{truncate(alert.description ?? "No description provided.", 86)}</p>
        </div>
      );
    },
  },
  {
    accessorKey: "source",
    header: "Source",
    cell: ({ row }) => (
      <div className="space-y-1">
        <Badge tone="medium">{row.original.source}</Badge>
        <p className="text-xs text-[#8f8f8f]">{row.original.source_type}</p>
      </div>
    ),
  },
  {
    accessorKey: "severity",
    header: "Severity",
    cell: ({ row }) => <Badge tone={row.original.severity}>{row.original.severity}</Badge>,
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => <Badge tone={row.original.status}>{row.original.status}</Badge>,
  },
  {
    accessorKey: "risk_score",
    header: "Risk",
    cell: ({ row }) => (
      <div className="space-y-2">
        <Badge tone={scoreTone(row.original.risk_score)}>{row.original.risk_score.toFixed(1)}</Badge>
        <ExplainabilityPopover alert={row.original} />
      </div>
    ),
  },
  {
    accessorKey: "asset",
    header: "Asset",
    cell: ({ row }) => (
      <div>
        <p className="font-medium text-[#111111]">{row.original.asset?.hostname ?? "Unmapped asset"}</p>
        <p className="text-xs text-[#8f8f8f]">{row.original.assignee?.full_name ?? "Unassigned"}</p>
      </div>
    ),
  },
  {
    accessorKey: "detected_at",
    header: "Detected",
    cell: ({ row }) => formatDate(row.original.detected_at),
  },
];

export default function AlertsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [severity, setSeverity] = useState("");
  const [source, setSource] = useState("");
  const [sourceType, setSourceType] = useState("");
  const deferredSearch = useDeferredValue(search);

  const query = useQuery({
    queryKey: ["alerts", page, deferredSearch, status, severity, source, sourceType],
    queryFn: () =>
      api.get<PageResult<Alert>>(
        `/alerts${createQueryString({
          page,
          page_size: 12,
          q: deferredSearch,
          status,
          severity,
          source,
          source_type: sourceType,
        })}`,
      ),
  });

  const resetFilters = () => {
    setPage(1);
    setSearch("");
    setStatus("");
    setSeverity("");
    setSource("");
    setSourceType("");
  };

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Alert triage"
        title="Alerts"
        description="Search, filter, prioritize, and hand off live alert records with explainable risk context and rapid escalation into incidents."
        actions={
          <Button variant="outline" onClick={resetFilters}>
            Clear filters
          </Button>
        }
      />

      <Card>
        <CardContent className="grid gap-3 lg:grid-cols-[1.2fr_repeat(4,minmax(0,1fr))]">
          <Input
            value={search}
            onChange={(event) => {
              setPage(1);
              setSearch(event.target.value);
            }}
            placeholder="Search alert title or description"
          />
          <Select value={status} onChange={(event) => { setPage(1); setStatus(event.target.value); }}>
            <option value="">All statuses</option>
            <option value="open">Open</option>
            <option value="triaged">Triaged</option>
            <option value="investigating">Investigating</option>
            <option value="resolved">Resolved</option>
            <option value="suppressed">Suppressed</option>
          </Select>
          <Select value={severity} onChange={(event) => { setPage(1); setSeverity(event.target.value); }}>
            <option value="">All severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </Select>
          <Select value={source} onChange={(event) => { setPage(1); setSource(event.target.value); }}>
            <option value="">All sources</option>
            <option value="wazuh">Wazuh</option>
            <option value="suricata">Suricata</option>
            <option value="nmap">Nmap import</option>
            <option value="hydra">Hydra import</option>
          </Select>
          <Select value={sourceType} onChange={(event) => { setPage(1); setSourceType(event.target.value); }}>
            <option value="">All source types</option>
            <option value="endpoint-telemetry">Endpoint telemetry</option>
            <option value="network-telemetry">Network telemetry</option>
            <option value="lab-import">Lab import</option>
            <option value="telemetry">Generic telemetry</option>
          </Select>
        </CardContent>
      </Card>

      {query.isLoading ? (
        <LoadingState lines={8} compact />
      ) : query.isError || !query.data ? (
        <ErrorState description={query.error instanceof Error ? query.error.message : "Alerts could not be loaded."} onRetry={() => query.refetch()} />
      ) : (
        <div className="space-y-4">
          <DataTable
            columns={columns}
            rows={query.data.items}
            emptyTitle="No alerts found"
            emptyMessage="Try broadening the filters or wait for new telemetry imports to arrive."
          />
          <PaginationControls page={query.data.page} pageSize={query.data.page_size} total={query.data.total} onPageChange={setPage} />
        </div>
      )}
    </div>
  );
}
