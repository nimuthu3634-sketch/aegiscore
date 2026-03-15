import { useEffect, useMemo, useState } from "react";

import { PlugIcon, ShieldIcon } from "@/components/Icons";
import { SectionCard } from "@/components/SectionCard";
import { StatusBadge } from "@/components/StatusBadge";
import { integrations as integrationMetadata } from "@/data/mock";
import { suricataDemoEvents } from "@/data/suricataDemoEvents";
import { wazuhDemoAlerts } from "@/data/wazuhDemoAlerts";
import { useAuth } from "@/hooks/useAuth";
import {
  fetchIntegrationStatuses,
  fetchSuricataIntegrationStatus,
  fetchWazuhIntegrationStatus,
  importSuricataEvents,
  importWazuhAlerts,
} from "@/services/api";
import type { UserRole } from "@/types/auth";
import type {
  IntegrationApiRecord,
  SourceToolKey,
  SuricataIntegrationStatus,
  WazuhIntegrationStatus,
} from "@/types/domain";

function formatDateTime(value: string | null) {
  if (!value) {
    return "Awaiting import";
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function canImportPrimaryIntegrations(userRole: UserRole | undefined) {
  return userRole === "admin" || userRole === "analyst";
}

const toolNameLookup: Record<string, SourceToolKey> = {
  Wazuh: "wazuh",
  Suricata: "suricata",
  Nmap: "nmap",
  Hydra: "hydra",
  VirtualBox: "virtualbox",
};

type ImportableTool = "wazuh" | "suricata";

export function IntegrationsPage() {
  const { token, user } = useAuth();
  const [integrationStatuses, setIntegrationStatuses] = useState<IntegrationApiRecord[]>([]);
  const [wazuhStatus, setWazuhStatus] = useState<WazuhIntegrationStatus | null>(null);
  const [suricataStatus, setSuricataStatus] = useState<SuricataIntegrationStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeImportTool, setActiveImportTool] = useState<ImportableTool | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [importMessage, setImportMessage] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    if (!token) {
      return;
    }

    let isActive = true;
    setIsLoading(true);
    setError(null);

    void Promise.all([
      fetchIntegrationStatuses(token),
      fetchWazuhIntegrationStatus(token),
      fetchSuricataIntegrationStatus(token),
    ])
      .then(([statuses, wazuh, suricata]) => {
        if (!isActive) {
          return;
        }

        setIntegrationStatuses(statuses);
        setWazuhStatus(wazuh);
        setSuricataStatus(suricata);
      })
      .catch((requestError: unknown) => {
        if (!isActive) {
          return;
        }

        setError(
          requestError instanceof Error
            ? requestError.message
            : "Integration status could not be loaded.",
        );
      })
      .finally(() => {
        if (isActive) {
          setIsLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [token, reloadKey]);

  const handleImportSampleData = async (tool: ImportableTool) => {
    if (!token) {
      return;
    }

    setActiveImportTool(tool);
    setImportMessage(null);

    try {
      const response =
        tool === "wazuh"
          ? await importWazuhAlerts(token, { alerts: wazuhDemoAlerts })
          : await importSuricataEvents(token, { events: suricataDemoEvents });

      setImportMessage(
        `${response.message} ${response.skipped_count > 0 ? `${response.skipped_count} duplicate payloads were skipped.` : ""}`.trim(),
      );
      setReloadKey((currentValue) => currentValue + 1);
    } catch (requestError) {
      setImportMessage(
        requestError instanceof Error
          ? requestError.message
          : "Sample import could not be completed.",
      );
    } finally {
      setActiveImportTool(null);
    }
  };

  const mergedIntegrations = useMemo(() => {
    const statusLookup = new Map(integrationStatuses.map((item) => [item.tool_name, item]));

    return integrationMetadata.map((integration) => ({
      ...integration,
      apiStatus: statusLookup.get(toolNameLookup[integration.name]),
    }));
  }, [integrationStatuses]);

  const canImport = canImportPrimaryIntegrations(user?.role);

  return (
    <div className="space-y-6">
      <SectionCard
        title="Integration readiness"
        description="Monitor primary telemetry sources and import safe demo data from Wazuh and Suricata to populate alerts and logs for presentations."
        eyebrow="Integrations"
        action={
          <button
            type="button"
            onClick={() => setReloadKey((currentValue) => currentValue + 1)}
            className="btn-primary"
            disabled={isLoading}
          >
            {isLoading ? "Refreshing..." : "Refresh status"}
          </button>
        }
      >
        {error ? (
          <div className="rounded-[1.5rem] border border-red-200 bg-red-50 px-4 py-5 text-sm text-red-700">
            {error}
          </div>
        ) : null}

        {importMessage ? (
          <div className="mb-4 rounded-[1.5rem] border border-brand-orange/15 bg-brand-orange/5 px-4 py-4 text-sm text-brand-black/75">
            {importMessage}
          </div>
        ) : null}

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {mergedIntegrations.map((integration) => {
            const liveStatus = integration.apiStatus;
            const isWazuh = integration.name === "Wazuh";
            const isSuricata = integration.name === "Suricata";
            const detailedStatus = isWazuh ? wazuhStatus : isSuricata ? suricataStatus : null;

            return (
              <div
                key={integration.id}
                className="rounded-[1.75rem] border border-brand-black/8 bg-white p-5 shadow-sm"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-light text-brand-orange">
                    <PlugIcon className="h-5 w-5" />
                  </div>
                  <StatusBadge variant={liveStatus?.status ?? integration.status}>
                    {liveStatus?.status ?? integration.status}
                  </StatusBadge>
                </div>

                <div className="mt-5">
                  <p className="text-lg font-semibold text-brand-black">{integration.name}</p>
                  <p className="mt-1 text-sm text-brand-black/55">{integration.vendor}</p>
                </div>

                <p className="mt-4 text-sm leading-6 text-brand-black/70">{integration.description}</p>

                <div className="mt-5 rounded-[1.25rem] bg-brand-light/70 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Last sync</p>
                  <p className="mt-2 text-sm font-medium text-brand-black">
                    {liveStatus ? formatDateTime(liveStatus.last_sync_at) : integration.lastSync}
                  </p>

                  {detailedStatus ? (
                    <div className="mt-4 space-y-3 text-sm text-brand-black/70">
                      <div className="flex justify-between gap-4">
                        <span>Imported alerts</span>
                        <span className="font-semibold text-brand-black">
                          {detailedStatus.imported_alert_count}
                        </span>
                      </div>
                      <div className="flex justify-between gap-4">
                        <span>Imported logs</span>
                        <span className="font-semibold text-brand-black">
                          {detailedStatus.imported_log_count}
                        </span>
                      </div>
                      <div className="flex justify-between gap-4">
                        <span>Last import</span>
                        <span className="font-semibold text-brand-black">
                          {formatDateTime(detailedStatus.last_import_at)}
                        </span>
                      </div>
                    </div>
                  ) : null}

                  {integration.note ? (
                    <p className="mt-3 text-xs font-semibold uppercase tracking-[0.18em] text-brand-orange">
                      {integration.note}
                    </p>
                  ) : null}
                </div>

                {detailedStatus ? (
                  <div className="mt-5 space-y-3">
                    <button
                      type="button"
                      onClick={() => handleImportSampleData(isWazuh ? "wazuh" : "suricata")}
                      className="btn-primary w-full"
                      disabled={
                        !canImport ||
                        activeImportTool !== null
                      }
                    >
                      {activeImportTool === (isWazuh ? "wazuh" : "suricata")
                        ? "Importing sample data..."
                        : "Import sample data"}
                    </button>
                    <p className="text-xs leading-5 text-brand-black/55">
                      {canImport
                        ? `${detailedStatus.available_demo_payloads} ${integration.name}-style demo ${
                            isWazuh ? "alerts" : "events"
                          } are ready to import into alerts and logs.`
                        : "Viewer accounts can inspect status, but only admins and analysts can run demo imports."}
                    </p>
                    {detailedStatus.last_import_message ? (
                      <div className="rounded-[1.25rem] border border-brand-black/8 bg-brand-light/60 px-4 py-3 text-xs leading-5 text-brand-black/65">
                        {detailedStatus.last_import_message}
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      </SectionCard>

      <SectionCard
        title="Primary telemetry workflow"
        description="Wazuh and Suricata remain the main demo-ready import paths for host and network visibility inside AegisCore."
        tone="dark"
      >
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-[1.5rem] border border-brand-white/10 bg-brand-white/5 p-5">
            <div className="flex items-center gap-3">
              <ShieldIcon className="h-5 w-5 text-brand-orange" />
              <p className="font-semibold text-white">Wazuh host telemetry</p>
            </div>
            <p className="mt-3 text-sm leading-6 text-brand-muted">
              Wazuh-style alert JSON can be imported on demand to create AegisCore alerts and
              normalized log entries from endpoint and agent events.
            </p>
            <div className="mt-4 space-y-2 text-sm text-brand-muted">
              {wazuhStatus?.latest_imported_alert_titles.length ? (
                wazuhStatus.latest_imported_alert_titles.map((title) => (
                  <div key={title} className="rounded-[1rem] bg-brand-white/5 px-3 py-2">
                    {title}
                  </div>
                ))
              ) : (
                <p>No imported Wazuh demo alerts yet.</p>
              )}
            </div>
          </div>

          <div className="rounded-[1.5rem] border border-brand-white/10 bg-brand-white/5 p-5">
            <p className="font-semibold text-white">Suricata network telemetry</p>
            <p className="mt-3 text-sm leading-6 text-brand-muted">
              Suricata EVE-style network events can be imported as demo data to create normalized
              logs and network alert records for threat-hunting presentations.
            </p>
            <div className="mt-4 space-y-2 text-sm text-brand-muted">
              {suricataStatus?.latest_imported_alert_titles.length ? (
                suricataStatus.latest_imported_alert_titles.map((title) => (
                  <div key={title} className="rounded-[1rem] bg-brand-white/5 px-3 py-2">
                    {title}
                  </div>
                ))
              ) : (
                <p>No imported Suricata demo alerts yet.</p>
              )}
            </div>
          </div>
        </div>
      </SectionCard>
    </div>
  );
}
