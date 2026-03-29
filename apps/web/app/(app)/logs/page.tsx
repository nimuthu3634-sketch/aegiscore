"use client";

import { type ColumnDef } from "@tanstack/react-table";
import { useQuery } from "@tanstack/react-query";
import { useDeferredValue, useState } from "react";

import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { PageHeader } from "@/components/shared/page-header";
import { PaginationControls } from "@/components/shared/pagination-controls";
import { DataTable } from "@/components/tables/data-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { api, createQueryString } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { LogEntry, PageResult } from "@/types/domain";

const columns: ColumnDef<LogEntry>[] = [
  {
    accessorKey: "event_timestamp",
    header: "Timestamp",
    cell: ({ row }) => formatDate(row.original.event_timestamp),
  },
  {
    accessorKey: "source",
    header: "Source",
    cell: ({ row }) => (
      <div className="space-y-1">
        <Badge tone="medium">{row.original.source}</Badge>
        <p className="text-xs text-[#8f8f8f]">{row.original.level}</p>
      </div>
    ),
  },
  {
    accessorKey: "asset",
    header: "Asset",
    cell: ({ row }) => row.original.asset?.hostname ?? "Unmapped asset",
  },
  {
    accessorKey: "category",
    header: "Category",
    cell: ({ row }) => row.original.category ?? "Uncategorized",
  },
  {
    accessorKey: "message",
    header: "Message",
    cell: ({ row }) => <span className="max-w-[420px] text-sm text-[#111111]">{row.original.message}</span>,
  },
];

export default function LogsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [source, setSource] = useState("");
  const [category, setCategory] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [selectedLogId, setSelectedLogId] = useState<string>("");
  const [payloadTab, setPayloadTab] = useState<"parsed" | "raw">("parsed");
  const deferredSearch = useDeferredValue(search);

  const query = useQuery({
    queryKey: ["logs", page, deferredSearch, source, category, start, end],
    queryFn: () =>
      api.get<PageResult<LogEntry>>(
        `/logs${createQueryString({
          page,
          page_size: 12,
          q: deferredSearch,
          source,
          category,
          start: start || undefined,
          end: end || undefined,
        })}`,
      ),
  });

  const selectedLog = query.data?.items.find((entry) => entry.id === selectedLogId) ?? query.data?.items[0] ?? null;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Structured search"
        title="Logs explorer"
        description="Search imported telemetry by source, category, date range, and payload representation without losing the raw event context."
      />

      <Card>
        <CardContent className="grid gap-3 lg:grid-cols-[1.3fr_repeat(4,minmax(0,1fr))]">
          <Input value={search} onChange={(event) => { setPage(1); setSearch(event.target.value); }} placeholder="Search message or category" />
          <Select value={source} onChange={(event) => { setPage(1); setSource(event.target.value); }}>
            <option value="">All sources</option>
            <option value="wazuh">Wazuh</option>
            <option value="suricata">Suricata</option>
            <option value="nmap">Nmap import</option>
            <option value="hydra">Hydra import</option>
          </Select>
          <Input value={category} onChange={(event) => { setPage(1); setCategory(event.target.value); }} placeholder="Category" />
          <Input type="datetime-local" value={start} onChange={(event) => { setPage(1); setStart(event.target.value); }} />
          <Input type="datetime-local" value={end} onChange={(event) => { setPage(1); setEnd(event.target.value); }} />
        </CardContent>
      </Card>

      {query.isLoading ? (
        <LoadingState lines={7} compact />
      ) : query.isError || !query.data ? (
        <ErrorState description={query.error instanceof Error ? query.error.message : "Logs could not be loaded."} onRetry={() => query.refetch()} />
      ) : (
        <div className="space-y-4">
          <DataTable
            columns={columns}
            rows={query.data.items}
            emptyTitle="No log entries found"
            emptyMessage="Try widening the search or import additional telemetry data."
          />

          {query.data.items.length ? (
            <Card>
              <CardHeader>
                <CardTitle>Selected log entry</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  {query.data.items.map((entry) => (
                    <Button key={entry.id} variant={selectedLog?.id === entry.id ? "default" : "outline"} size="sm" onClick={() => setSelectedLogId(entry.id)}>
                      {formatDate(entry.event_timestamp)}
                    </Button>
                  ))}
                </div>

                {selectedLog ? (
                  <>
                    <div className="rounded-[1.25rem] border bg-[#fcfcfc] p-4">
                      <p className="font-semibold text-[#111111]">{selectedLog.message}</p>
                      <p className="mt-2 text-sm text-[#6f6f6f]">
                        {selectedLog.source} / {selectedLog.category ?? "uncategorized"} / {selectedLog.asset?.hostname ?? "unmapped"}
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button variant={payloadTab === "parsed" ? "default" : "outline"} size="sm" onClick={() => setPayloadTab("parsed")}>
                        Parsed view
                      </Button>
                      <Button variant={payloadTab === "raw" ? "default" : "outline"} size="sm" onClick={() => setPayloadTab("raw")}>
                        Raw view
                      </Button>
                    </div>

                    <pre className="overflow-x-auto rounded-[1.5rem] border bg-[#111111] p-5 text-xs leading-6 text-white">
                      {JSON.stringify(payloadTab === "parsed" ? selectedLog.parsed_payload : selectedLog.raw_payload, null, 2)}
                    </pre>
                  </>
                ) : null}
              </CardContent>
            </Card>
          ) : null}

          <PaginationControls page={query.data.page} pageSize={query.data.page_size} total={query.data.total} onPageChange={setPage} />
        </div>
      )}
    </div>
  );
}
