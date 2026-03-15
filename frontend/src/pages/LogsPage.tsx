import { useEffect, useMemo, useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/DataTable";
import { ArrowUpRightIcon, LogIcon } from "@/components/Icons";
import { SectionCard } from "@/components/SectionCard";
import { SeverityBadge } from "@/components/SeverityBadge";
import { StatusBadge } from "@/components/StatusBadge";
import { logIngestSamples } from "@/data/logIngestSamples";
import { useAuth } from "@/hooks/useAuth";
import { fetchLogById, fetchLogs, ingestLog } from "@/services/api";
import type { UserRole } from "@/types/auth";
import type { LogEntryRecord, LogListResponse } from "@/types/domain";

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatTitle(value: string) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function canIngestLogs(userRole: UserRole | undefined) {
  return userRole === "admin" || userRole === "analyst";
}

function getLabOnlyNote(sourceTool: string) {
  if (sourceTool === "nmap") {
    return "Imported lab assessment results only";
  }

  if (sourceTool === "hydra") {
    return "Imported lab credential assessment results only";
  }

  return null;
}

const logColumns: DataTableColumn<LogEntryRecord>[] = [
  {
    key: "source_tool",
    header: "Source Tool",
    render: (log) => (
      <div>
        <p className="font-semibold text-brand-black">{formatTitle(log.source_tool)}</p>
        <p className="mt-1 text-xs text-brand-black/50">{log.source}</p>
      </div>
    ),
  },
  {
    key: "event_type",
    header: "Event Type",
    render: (log) => (
      <span className="inline-flex rounded-full bg-brand-light px-3 py-1 text-xs font-semibold text-brand-black/70">
        {formatTitle(log.event_type)}
      </span>
    ),
  },
  {
    key: "severity",
    header: "Severity",
    render: (log) => <SeverityBadge level={log.severity} />,
  },
  {
    key: "created_at",
    header: "Timestamp",
    render: (log) => <span>{formatDateTime(log.created_at)}</span>,
  },
];

export function LogsPage() {
  const { token, user } = useAuth();
  const [logsResponse, setLogsResponse] = useState<LogListResponse | null>(null);
  const [selectedLogId, setSelectedLogId] = useState<string | null>(null);
  const [selectedLog, setSelectedLog] = useState<LogEntryRecord | null>(null);
  const [listLoading, setListLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [ingestLoading, setIngestLoading] = useState(false);
  const [listError, setListError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [ingestMessage, setIngestMessage] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    if (!token) {
      return;
    }

    let isActive = true;
    setListLoading(true);
    setListError(null);

    void fetchLogs(token)
      .then((response) => {
        if (!isActive) {
          return;
        }

        setLogsResponse(response);
        setSelectedLogId((currentId) => {
          if (response.items.length === 0) {
            return null;
          }

          if (currentId && response.items.some((item) => item.id === currentId)) {
            return currentId;
          }

          return response.items[0]?.id ?? null;
        });
      })
      .catch((requestError: unknown) => {
        if (!isActive) {
          return;
        }

        setListError(
          requestError instanceof Error ? requestError.message : "The log feed could not be loaded.",
        );
      })
      .finally(() => {
        if (isActive) {
          setListLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [token, reloadKey]);

  useEffect(() => {
    if (!token || !selectedLogId) {
      setSelectedLog(null);
      setDetailError(null);
      return;
    }

    let isActive = true;
    setDetailLoading(true);
    setDetailError(null);

    void fetchLogById(token, selectedLogId)
      .then((response) => {
        if (!isActive) {
          return;
        }

        setSelectedLog(response);
      })
      .catch((requestError: unknown) => {
        if (!isActive) {
          return;
        }

        setDetailError(
          requestError instanceof Error ? requestError.message : "The log detail could not be loaded.",
        );
      })
      .finally(() => {
        if (isActive) {
          setDetailLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [token, selectedLogId, reloadKey]);

  const handleRefresh = () => {
    setReloadKey((currentValue) => currentValue + 1);
  };

  const handleIngestSamples = async () => {
    if (!token) {
      return;
    }

    setIngestLoading(true);
    setIngestMessage(null);

    try {
      const ingestedLogs = await Promise.all(logIngestSamples.map((sample) => ingestLog(token, sample)));
      const latestLog = ingestedLogs[ingestedLogs.length - 1];
      setSelectedLogId(latestLog?.id ?? null);
      setIngestMessage(`${ingestedLogs.length} payloads ingested into the log feed.`);
      setReloadKey((currentValue) => currentValue + 1);
    } catch (requestError) {
      setIngestMessage(
        requestError instanceof Error
          ? requestError.message
          : "Payload ingestion could not be completed.",
      );
    } finally {
      setIngestLoading(false);
    }
  };

  const logs = logsResponse?.items ?? [];
  const canIngest = canIngestLogs(user?.role);
  const selectedLabOnlyNote = selectedLog ? getLabOnlyNote(selectedLog.source_tool) : null;
  const sourceToolCount = useMemo(() => new Set(logs.map((log) => log.source_tool)).size, [logs]);
  const latestTimestamp = logs[0]?.created_at;

  return (
    <div className="space-y-6">
      <SectionCard
        title="Log ingestion and normalization"
        description="Review the live security event feed, compare raw versus normalized payloads, and import authorized sample events."
        eyebrow="Logs"
        tone="dark"
        action={
          <div className="flex flex-col gap-3 sm:flex-row">
            <button
              type="button"
              onClick={handleIngestSamples}
              className="btn-primary inline-flex items-center gap-2"
              disabled={!canIngest || ingestLoading}
            >
              {ingestLoading ? "Ingesting..." : "Ingest payloads"}
              <ArrowUpRightIcon className="h-4 w-4" />
            </button>
            <button type="button" onClick={handleRefresh} className="btn-secondary" disabled={listLoading}>
              {listLoading ? "Refreshing..." : "Refresh feed"}
            </button>
          </div>
        }
      >
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-[1.5rem] border border-brand-white/10 bg-brand-white/5 p-5">
            <p className="text-xs uppercase tracking-[0.2em] text-brand-muted">Stored logs</p>
            <p className="mt-3 text-3xl font-semibold text-white">{logsResponse?.total_items ?? 0}</p>
            <p className="mt-2 text-sm text-brand-muted">Normalized events ready for analyst review</p>
          </div>
          <div className="rounded-[1.5rem] border border-brand-white/10 bg-brand-white/5 p-5">
            <p className="text-xs uppercase tracking-[0.2em] text-brand-muted">Source tools</p>
            <p className="mt-3 text-3xl font-semibold text-white">{sourceToolCount}</p>
            <p className="mt-2 text-sm text-brand-muted">Coverage across telemetry and imported assessment artifacts</p>
          </div>
          <div className="rounded-[1.5rem] border border-brand-white/10 bg-brand-white/5 p-5">
            <p className="text-xs uppercase tracking-[0.2em] text-brand-muted">Latest ingest</p>
            <p className="mt-3 text-lg font-semibold text-white">
              {latestTimestamp ? formatDateTime(latestTimestamp) : "No logs yet"}
            </p>
            <p className="mt-2 text-sm text-brand-muted">
              Timestamps are normalized to a consistent UTC format
            </p>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <StatusBadge variant={listError ? "degraded" : "connected"}>
            {listError ? "feed issue" : "log api connected"}
          </StatusBadge>
          {!canIngest ? <StatusBadge variant="pending">viewer read only</StatusBadge> : null}
        </div>

        {ingestMessage ? (
          <div className="mt-4 rounded-[1.25rem] border border-brand-orange/15 bg-brand-orange/5 px-4 py-3 text-sm text-brand-muted">
            {ingestMessage}
          </div>
        ) : null}
      </SectionCard>

      <div className="grid gap-6 xl:grid-cols-[1.3fr_1fr]">
        <SectionCard
          title="Log feed"
          description="Source tool, normalized event type, severity, and timestamp for ingested events."
        >
          {listError ? (
            <div className="space-y-4">
              <div className="rounded-[1.5rem] border border-red-200 bg-red-50 px-4 py-5 text-sm text-red-700">
                {listError}
              </div>
              <button type="button" onClick={handleRefresh} className="btn-primary">
                Retry logs
              </button>
            </div>
          ) : listLoading && !logsResponse ? (
            <div className="h-80 animate-pulse rounded-[1.5rem] bg-brand-light/70" />
          ) : (
            <DataTable
              columns={logColumns}
              rows={logs}
              rowKey={(log) => log.id}
              onRowClick={(log) => setSelectedLogId(log.id)}
              selectedRowKey={selectedLogId ?? undefined}
              emptyMessage="No ingested logs are available yet."
            />
          )}
        </SectionCard>

        <SectionCard
          title="Log detail"
          description="Compare the original raw event payload with its normalized AegisCore representation."
        >
          {!selectedLogId && !listLoading ? (
            <div className="rounded-[1.5rem] border border-dashed border-brand-black/10 bg-brand-light/50 p-10 text-center text-sm text-brand-black/55">
              Select a log entry to inspect its raw and normalized payloads.
            </div>
          ) : detailLoading && !selectedLog ? (
            <div className="h-80 animate-pulse rounded-[1.5rem] bg-brand-light/70" />
          ) : detailError ? (
            <div className="space-y-4">
              <div className="rounded-[1.5rem] border border-red-200 bg-red-50 px-4 py-5 text-sm text-red-700">
                {detailError}
              </div>
              <button type="button" onClick={handleRefresh} className="btn-secondary">
                Retry detail
              </button>
            </div>
          ) : selectedLog ? (
            <div className="space-y-4">
              <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-brand-orange">
                      <LogIcon className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-[0.24em] text-brand-orange">
                        {selectedLog.id}
                      </p>
                      <h3 className="mt-2 text-xl font-semibold text-brand-black">
                        {formatTitle(selectedLog.event_type)}
                      </h3>
                      <p className="mt-2 text-sm text-brand-black/60">
                        {formatTitle(selectedLog.source_tool)} from {selectedLog.source}
                      </p>
                    </div>
                  </div>
                  <SeverityBadge level={selectedLog.severity} />
                </div>
              </div>

              {selectedLabOnlyNote ? (
                <div className="rounded-[1.5rem] border border-brand-orange/20 bg-brand-orange/5 px-4 py-4 text-sm text-brand-black/70">
                  {selectedLabOnlyNote}. This log is presented as a safe imported assessment result,
                  not an offensive automation workflow.
                </div>
              ) : null}

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-[1.5rem] border border-brand-black/8 bg-white p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Severity</p>
                  <div className="mt-3">
                    <SeverityBadge level={selectedLog.severity} />
                  </div>
                </div>
                <div className="rounded-[1.5rem] border border-brand-black/8 bg-white p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Timestamp</p>
                  <p className="mt-3 text-sm font-semibold text-brand-black">
                    {formatDateTime(selectedLog.created_at)}
                  </p>
                </div>
              </div>

              <div className="grid gap-4 lg:grid-cols-2">
                <div className="rounded-[1.5rem] border border-brand-black/8 bg-white p-4">
                  <p className="text-sm font-semibold text-brand-black">Raw log payload</p>
                  <pre className="mt-4 overflow-x-auto rounded-[1.25rem] bg-brand-surface p-4 text-xs leading-6 text-brand-muted">
                    {JSON.stringify(selectedLog.raw_log, null, 2)}
                  </pre>
                </div>

                <div className="rounded-[1.5rem] border border-brand-black/8 bg-white p-4">
                  <p className="text-sm font-semibold text-brand-black">Normalized log payload</p>
                  <pre className="mt-4 overflow-x-auto rounded-[1.25rem] bg-brand-surface p-4 text-xs leading-6 text-brand-muted">
                    {JSON.stringify(selectedLog.normalized_log, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          ) : null}
        </SectionCard>
      </div>
    </div>
  );
}
