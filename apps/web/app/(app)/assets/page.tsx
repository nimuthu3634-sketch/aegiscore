"use client";

import Link from "next/link";
import { type ColumnDef } from "@tanstack/react-table";
import { useQuery } from "@tanstack/react-query";
import { useDeferredValue, useState } from "react";

import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { PageHeader } from "@/components/shared/page-header";
import { PaginationControls } from "@/components/shared/pagination-controls";
import { DataTable } from "@/components/tables/data-table";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { api, createQueryString } from "@/lib/api";
import { formatDate, scoreTone } from "@/lib/format";
import type { Asset, PageResult } from "@/types/domain";

const columns: ColumnDef<Asset>[] = [
  {
    accessorKey: "hostname",
    header: "Host",
    cell: ({ row }) => (
      <div className="space-y-1">
        <Link href={`/assets/${row.original.id}`} className="font-semibold text-[#111111] hover:text-[#FF7A1A]">
          {row.original.hostname}
        </Link>
        <p className="text-sm text-[#6f6f6f]">{row.original.ip_address ?? "IP unavailable"}</p>
      </div>
    ),
  },
  {
    accessorKey: "operating_system",
    header: "Operating system",
    cell: ({ row }) => row.original.operating_system ?? "Unknown",
  },
  {
    accessorKey: "criticality",
    header: "Criticality",
    cell: ({ row }) => <span className="font-medium">{row.original.criticality}</span>,
  },
  {
    accessorKey: "risk_score",
    header: "Risk posture",
    cell: ({ row }) => (
      <div className="space-y-1">
        <Badge tone={scoreTone(row.original.risk_score)}>{row.original.risk_score.toFixed(1)}</Badge>
        <p className="max-w-[280px] text-xs text-[#8f8f8f]">{row.original.risk_summary ?? "No active summary"}</p>
      </div>
    ),
  },
  {
    accessorKey: "last_seen_at",
    header: "Last seen",
    cell: ({ row }) => formatDate(row.original.last_seen_at),
  },
];

export default function AssetsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [riskMin, setRiskMin] = useState("");
  const deferredSearch = useDeferredValue(search);

  const query = useQuery({
    queryKey: ["assets", page, deferredSearch, riskMin],
    queryFn: () =>
      api.get<PageResult<Asset>>(
        `/assets${createQueryString({
          page,
          page_size: 12,
          q: deferredSearch,
          risk_min: riskMin || undefined,
        })}`,
      ),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Endpoint inventory"
        title="Assets"
        description="Track host visibility, risk posture, last-seen context, and the alerts or incidents attached to each asset record."
      />

      <Card>
        <CardContent className="grid gap-3 lg:grid-cols-[1.5fr_220px]">
          <Input value={search} onChange={(event) => { setPage(1); setSearch(event.target.value); }} placeholder="Search hostname or IP address" />
          <Select value={riskMin} onChange={(event) => { setPage(1); setRiskMin(event.target.value); }}>
            <option value="">All risk levels</option>
            <option value="65">Risk 65+</option>
            <option value="35">Risk 35+</option>
            <option value="1">Risk 1+</option>
          </Select>
        </CardContent>
      </Card>

      {query.isLoading ? (
        <LoadingState lines={7} compact />
      ) : query.isError || !query.data ? (
        <ErrorState description={query.error instanceof Error ? query.error.message : "Assets could not be loaded."} onRetry={() => query.refetch()} />
      ) : (
        <div className="space-y-4">
          <DataTable
            columns={columns}
            rows={query.data.items}
            emptyTitle="No assets available"
            emptyMessage="Assets will appear here after alert creation or telemetry imports associate host information."
          />
          <PaginationControls page={query.data.page} pageSize={query.data.page_size} total={query.data.total} onPageChange={setPage} />
        </div>
      )}
    </div>
  );
}
