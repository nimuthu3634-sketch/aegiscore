"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { DataTable } from "@/components/tables/data-table";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { PageResult } from "@/types/domain";

type LogEntry = {
  id: string;
  source: string;
  level: string;
  category?: string | null;
  message: string;
  event_timestamp: string;
  raw_payload: Record<string, unknown>;
  parsed_payload: Record<string, unknown>;
  asset?: { hostname: string } | null;
};

export default function LogsPage() {
  const [query, setQuery] = useState("");
  const [source, setSource] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["logs", query, source],
    queryFn: () => api.get<PageResult<LogEntry>>(`/logs?q=${encodeURIComponent(query)}&source=${source}`),
  });

  return (
    <AppShell title="Log Explorer">
      <div className="space-y-5">
        <div className="grid gap-4 rounded-2xl border bg-white p-4 shadow-panel md:grid-cols-[1fr_220px]">
          <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search raw or parsed log content" />
          <Select value={source} onChange={(event) => setSource(event.target.value)}>
            <option value="">All sources</option>
            <option value="wazuh">Wazuh</option>
            <option value="suricata">Suricata</option>
            <option value="nmap">Nmap import</option>
            <option value="hydra">Hydra import</option>
          </Select>
        </div>
        {isLoading || !data ? (
          <div className="rounded-2xl border bg-white p-8 shadow-panel">Loading logs...</div>
        ) : (
          <div className="space-y-4">
            <DataTable
              rows={data.items}
              emptyMessage="No logs matched the current filters."
              columns={[
                { key: "time", header: "Time", render: (entry) => formatDate(entry.event_timestamp) },
                { key: "source", header: "Source", render: (entry) => entry.source },
                { key: "asset", header: "Asset", render: (entry) => entry.asset?.hostname ?? "Unmapped" },
                { key: "message", header: "Message", render: (entry) => entry.message },
              ]}
            />
            {data.items.slice(0, 3).map((entry) => (
              <Card key={entry.id}>
                <CardContent className="space-y-3 py-5">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-semibold">{entry.message}</p>
                      <p className="text-sm text-[var(--muted)]">
                        {entry.source} • {entry.category}
                      </p>
                    </div>
                  </div>
                  <div className="grid gap-4 lg:grid-cols-2">
                    <pre className="overflow-x-auto rounded-2xl border bg-[#111111] p-4 text-xs text-white">
                      {JSON.stringify(entry.parsed_payload, null, 2)}
                    </pre>
                    <pre className="overflow-x-auto rounded-2xl border bg-[#f8fafc] p-4 text-xs">
                      {JSON.stringify(entry.raw_payload, null, 2)}
                    </pre>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
