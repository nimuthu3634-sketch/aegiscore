import { useEffect, useMemo, useState } from "react";

import { VirtualLabSection } from "@/components/VirtualLabSection";
import { PlugIcon, ShieldIcon } from "@/components/Icons";
import { SectionCard } from "@/components/SectionCard";
import { StatusBadge } from "@/components/StatusBadge";
import { hydraDemoResults } from "@/data/hydraDemoResults";
import { integrations as integrationMetadata } from "@/data/mock";
import { nmapDemoResults } from "@/data/nmapDemoResults";
import { suricataDemoEvents } from "@/data/suricataDemoEvents";
import { wazuhDemoAlerts } from "@/data/wazuhDemoAlerts";
import { useAuth } from "@/hooks/useAuth";
import {
  fetchHydraIntegrationStatus,
  fetchIntegrationStatuses,
  fetchNmapIntegrationStatus,
  fetchSuricataIntegrationStatus,
  fetchWazuhIntegrationStatus,
  importHydraResults,
  importNmapResults,
  importSuricataEvents,
  importWazuhAlerts,
} from "@/services/api";
import type { UserRole } from "@/types/auth";
import type {
  HydraIntegrationStatus,
  IntegrationApiRecord,
  IntegrationImportResponse,
  IntegrationImportStatus,
  NmapIntegrationStatus,
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

function isImportableTool(value: SourceToolKey): value is ImportableTool {
  return value === "wazuh" || value === "suricata" || value === "nmap" || value === "hydra";
}

function isLabAssessmentTool(value: SourceToolKey) {
  return value === "nmap" || value === "hydra";
}

function getImportMetricLabel(tool: SourceToolKey) {
  return isLabAssessmentTool(tool) ? "Imported findings" : "Imported alerts";
}

function getDemoPayloadLabel(tool: ImportableTool) {
  if (tool === "wazuh") {
    return "alerts";
  }

  if (tool === "suricata") {
    return "events";
  }

  return "assessment result sets";
}

const toolNameLookup: Record<string, SourceToolKey> = {
  Wazuh: "wazuh",
  Suricata: "suricata",
  Nmap: "nmap",
  Hydra: "hydra",
  VirtualBox: "virtualbox",
};

type ImportableTool = "wazuh" | "suricata" | "nmap" | "hydra";

type WorkflowCard = {
  tool: ImportableTool;
  title: string;
  description: string;
  emptyState: string;
};

const workflowCards: WorkflowCard[] = [
  {
    tool: "wazuh",
    title: "Wazuh host telemetry",
    description:
      "Wazuh-style alert JSON can be imported on demand to create AegisCore alerts and normalized host log entries.",
    emptyState: "No imported Wazuh alerts yet.",
  },
  {
    tool: "suricata",
    title: "Suricata network telemetry",
    description:
      "Suricata EVE-style events can be imported to generate network alerts and normalized logs for operational review.",
    emptyState: "No imported Suricata alerts yet.",
  },
  {
    tool: "nmap",
    title: "Nmap assessment results",
    description:
      "Authorized Nmap result files are parsed into findings for service-exposure review. AegisCore does not run scans.",
    emptyState: "No imported Nmap assessment findings yet.",
  },
  {
    tool: "hydra",
    title: "Hydra assessment results",
    description:
      "Authorized Hydra result artifacts are imported as credential-assessment findings. No offensive automation is supported.",
    emptyState: "No imported Hydra assessment findings yet.",
  },
];

export function IntegrationsPage() {
  const { token, user } = useAuth();
  const [integrationStatuses, setIntegrationStatuses] = useState<IntegrationApiRecord[]>([]);
  const [wazuhStatus, setWazuhStatus] = useState<WazuhIntegrationStatus | null>(null);
  const [suricataStatus, setSuricataStatus] = useState<SuricataIntegrationStatus | null>(null);
  const [nmapStatus, setNmapStatus] = useState<NmapIntegrationStatus | null>(null);
  const [hydraStatus, setHydraStatus] = useState<HydraIntegrationStatus | null>(null);
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
      fetchNmapIntegrationStatus(token),
      fetchHydraIntegrationStatus(token),
    ])
      .then(([statuses, wazuh, suricata, nmap, hydra]) => {
        if (!isActive) {
          return;
        }

        setIntegrationStatuses(statuses);
        setWazuhStatus(wazuh);
        setSuricataStatus(suricata);
        setNmapStatus(nmap);
        setHydraStatus(hydra);
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
      let response: IntegrationImportResponse;

      if (tool === "wazuh") {
        response = await importWazuhAlerts(token, { alerts: wazuhDemoAlerts });
      } else if (tool === "suricata") {
        response = await importSuricataEvents(token, { events: suricataDemoEvents });
      } else if (tool === "nmap") {
        response = await importNmapResults(token, { results: nmapDemoResults });
      } else {
        response = await importHydraResults(token, { results: hydraDemoResults });
      }

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
      toolKey: toolNameLookup[integration.name],
      apiStatus: statusLookup.get(toolNameLookup[integration.name]),
    }));
  }, [integrationStatuses]);

  const detailedStatusLookup = useMemo<Record<ImportableTool, IntegrationImportStatus | null>>(
    () => ({
      wazuh: wazuhStatus,
      suricata: suricataStatus,
      nmap: nmapStatus,
      hydra: hydraStatus,
    }),
    [hydraStatus, nmapStatus, suricataStatus, wazuhStatus],
  );

  const canImport = canImportPrimaryIntegrations(user?.role);

  return (
    <div className="space-y-6">
      <SectionCard
        title="Integration readiness"
        description="Monitor host telemetry, network telemetry, authorized assessment-result imports, and the VirtualBox environment from one unified workspace."
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
            const toolKey = integration.toolKey;
            const importableTool = isImportableTool(toolKey) ? toolKey : null;
            const detailedStatus = importableTool ? detailedStatusLookup[importableTool] : null;
            const isVirtualBox = toolKey === "virtualbox";

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

                {integration.labOnly ? (
                  <div className="mt-4 flex flex-wrap gap-2">
                    <span className="rounded-full bg-brand-orange/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-brand-orange">
                      {integration.note ?? "Authorized assessment result ingestion"}
                    </span>
                    <span className="rounded-full bg-brand-black/5 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-brand-black/55">
                      No offensive automation
                    </span>
                  </div>
                ) : null}

                {isVirtualBox ? (
                  <div className="mt-4 flex flex-wrap gap-2">
                    <span className="rounded-full bg-brand-orange/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-brand-orange">
                      Visualization and tracking
                    </span>
                    <span className="rounded-full bg-brand-black/5 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-brand-black/55">
                      No direct VM control
                    </span>
                  </div>
                ) : null}

                <div className="mt-5 rounded-[1.25rem] bg-brand-light/70 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Last sync</p>
                  <p className="mt-2 text-sm font-medium text-brand-black">
                    {liveStatus ? formatDateTime(liveStatus.last_sync_at) : integration.lastSync}
                  </p>

                  {detailedStatus ? (
                    <div className="mt-4 space-y-3 text-sm text-brand-black/70">
                      <div className="flex justify-between gap-4">
                        <span>{getImportMetricLabel(toolKey)}</span>
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
                </div>

                {detailedStatus && importableTool ? (
                  <div className="mt-5 space-y-3">
                    <button
                      type="button"
                      onClick={() => handleImportSampleData(importableTool)}
                      className="btn-primary w-full"
                      disabled={!canImport || activeImportTool !== null}
                    >
                      {activeImportTool === importableTool
                        ? "Importing data..."
                        : "Import available data"}
                    </button>
                    <p className="text-xs leading-5 text-brand-black/55">
                      {canImport
                        ? `${detailedStatus.available_demo_payloads} ${getDemoPayloadLabel(importableTool)} are ready to import for ${integration.name} workflows.`
                        : "Viewer accounts can inspect status, but only admins and analysts can run imports."}
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
        title="Telemetry and assessment workflows"
        description="AegisCore keeps operational telemetry and authorized assessment imports in one unified view while preserving clear safety boundaries."
        tone="dark"
      >
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {workflowCards.map((card) => {
            const status = detailedStatusLookup[card.tool];
            const isLabOnly = card.tool === "nmap" || card.tool === "hydra";

            return (
              <div
                key={card.tool}
                className="rounded-[1.5rem] border border-brand-white/10 bg-brand-white/5 p-5"
              >
                <div className="flex items-center gap-3">
                  <ShieldIcon className="h-5 w-5 text-brand-orange" />
                  <p className="font-semibold text-white">{card.title}</p>
                </div>
                <p className="mt-3 text-sm leading-6 text-brand-muted">{card.description}</p>

                {isLabOnly ? (
                  <div className="mt-4 space-y-2">
                    <div className="rounded-[1rem] bg-brand-orange/10 px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-brand-orange">
                      Authorized assessment result ingestion
                    </div>
                    <div className="rounded-[1rem] bg-brand-white/5 px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-brand-muted">
                      No offensive automation
                    </div>
                  </div>
                ) : null}

                <div className="mt-4 space-y-2 text-sm text-brand-muted">
                  {status?.latest_imported_alert_titles.length ? (
                    status.latest_imported_alert_titles.map((title) => (
                      <div key={title} className="rounded-[1rem] bg-brand-white/5 px-3 py-2">
                        {title}
                      </div>
                    ))
                  ) : (
                    <p>{card.emptyState}</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </SectionCard>

      <VirtualLabSection
        token={token ?? null}
        canManage={canImport}
        refreshKey={reloadKey}
        onLabUpdated={() => setReloadKey((currentValue) => currentValue + 1)}
      />
    </div>
  );
}
