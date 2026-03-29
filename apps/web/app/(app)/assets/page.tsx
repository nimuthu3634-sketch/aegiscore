"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { DataTable } from "@/components/tables/data-table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { Asset, PageResult } from "@/types/domain";

export default function AssetsPage() {
  const [query, setQuery] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["assets", query],
    queryFn: () => api.get<PageResult<Asset>>(`/assets?q=${encodeURIComponent(query)}`),
  });

  return (
    <AppShell title="Assets and Endpoints">
      <div className="space-y-5">
        <div className="rounded-2xl border bg-white p-4 shadow-panel">
          <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search hostnames or IP addresses" />
        </div>
        {isLoading || !data ? (
          <div className="rounded-2xl border bg-white p-8 shadow-panel">Loading assets...</div>
        ) : (
          <DataTable
            rows={data.items}
            emptyMessage="No assets matched the current filters."
            columns={[
              {
                key: "host",
                header: "Hostname",
                render: (asset) => (
                  <Link className="font-semibold hover:text-[var(--accent)]" href={`/assets/${asset.id}`}>
                    {asset.hostname}
                  </Link>
                ),
              },
              { key: "ip", header: "IP address", render: (asset) => asset.ip_address ?? "Unknown" },
              { key: "lastSeen", header: "Last seen", render: (asset) => formatDate(asset.last_seen_at) },
              {
                key: "risk",
                header: "Risk posture",
                render: (asset) => (
                  <div className="flex items-center gap-2">
                    <Badge tone={asset.risk_score >= 65 ? "high" : asset.risk_score >= 35 ? "medium" : "low"}>{asset.risk_score}</Badge>
                    <span className="text-sm text-[var(--muted)]">{asset.risk_summary ?? "Baseline healthy"}</span>
                  </div>
                ),
              },
            ]}
          />
        )}
      </div>
    </AppShell>
  );
}
