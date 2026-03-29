"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { DataTable } from "@/components/tables/data-table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { Alert, PageResult } from "@/types/domain";

export default function AlertsPage() {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["alerts", query, status],
    queryFn: () => api.get<PageResult<Alert>>(`/alerts?q=${encodeURIComponent(query)}&status=${status}`),
  });

  return (
    <AppShell title="Alerts">
      <div className="space-y-5">
        <div className="grid gap-4 rounded-2xl border bg-white p-4 shadow-panel md:grid-cols-[1fr_220px]">
          <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search title or description" />
          <Select value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">All statuses</option>
            <option value="open">Open</option>
            <option value="triaged">Triaged</option>
            <option value="investigating">Investigating</option>
            <option value="resolved">Resolved</option>
          </Select>
        </div>
        {isLoading || !data ? (
          <div className="rounded-2xl border bg-white p-8 shadow-panel">Loading alerts...</div>
        ) : (
          <DataTable
            rows={data.items}
            emptyMessage="No alerts matched the current filters."
            columns={[
              {
                key: "title",
                header: "Alert",
                render: (alert) => (
                  <div>
                    <Link className="font-semibold hover:text-[var(--accent)]" href={`/alerts/${alert.id}`}>
                      {alert.title}
                    </Link>
                    <p className="mt-1 text-xs uppercase tracking-wide text-[var(--muted)]">{alert.source}</p>
                  </div>
                ),
              },
              {
                key: "severity",
                header: "Severity",
                render: (alert) => <Badge tone={alert.severity}>{alert.severity}</Badge>,
              },
              {
                key: "status",
                header: "Status",
                render: (alert) => <Badge tone={alert.status}>{alert.status}</Badge>,
              },
              {
                key: "risk",
                header: "Risk",
                render: (alert) => <span className="font-semibold">{alert.risk_score}</span>,
              },
              {
                key: "asset",
                header: "Asset",
                render: (alert) => alert.asset?.hostname ?? "Unmapped",
              },
              {
                key: "time",
                header: "Detected",
                render: (alert) => formatDate(alert.detected_at),
              },
            ]}
          />
        )}
      </div>
    </AppShell>
  );
}
