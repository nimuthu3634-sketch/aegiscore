import { useEffect, useState } from "react";

import { PlugIcon, ShieldIcon } from "@/components/Icons";
import { SectionCard } from "@/components/SectionCard";
import { StatusBadge } from "@/components/StatusBadge";
import { hydraDemoResults } from "@/data/hydraDemoResults";
import { nmapDemoResults } from "@/data/nmapDemoResults";
import { suricataDemoEvents } from "@/data/suricataDemoEvents";
import { wazuhDemoAlerts } from "@/data/wazuhDemoAlerts";
import { useAuth } from "@/hooks/useAuth";
import {
  fetchHydraIntegrationStatus,
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
  IntegrationImportResponse,
  NmapIntegrationStatus,
  SuricataIntegrationStatus,
  WazuhIntegrationStatus,
} from "@/types/domain";

type ImportableTool = "wazuh" | "suricata" | "nmap" | "hydra";

type IntegrationCard = {
  tool: ImportableTool;
  name: string;
  vendor: string;
  title: string;
  description: string;
  emptyState: string;
  labOnly?: boolean;
};

const integrationCards: IntegrationCard[] = [
  {
    tool: "wazuh",
    name: "Wazuh",
    vendor: "Endpoint telemetry",
    title: "Host monitoring and alert ingestion",
    description:
      "Wazuh alert JSON is normalized into SOC alerts and supporting log records for analyst triage.",
    emptyState: "No imported Wazuh alerts yet.",
  },
  {
    tool: "suricata",
    name: "Suricata",
    vendor: "Network IDS",
    title: "Network alert ingestion",
    description:
      "Suricata events are converted into normalized network telemetry and alert records for the dashboard.",
    emptyState: "No imported Suricata alerts yet.",
  },
  {
    tool: "nmap",
    name: "Nmap",
    vendor: "Lab result ingestion",
    title: "Authorized scan-result ingestion",
    description:
      "AegisCore parses imported Nmap findings for visualization only and does not execute scans.",
    emptyState: "No imported Nmap findings yet.",
    labOnly: true,
  },
  {
    tool: "hydra",
    name: "Hydra",
    vendor: "Lab result ingestion",
    title: "Authorized credential-result ingestion",
    description:
      "Imported Hydra result artifacts are stored as classroom-safe findings without offensive automation.",
    emptyState: "No imported Hydra findings yet.",
    labOnly: true,
  },
];

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

function getImportPayloadLabel(tool: ImportableTool) {
  if (tool === "wazuh") {
    return "alerts";
  }

  if (tool === "suricata") {
    return "events";
  }

  return "assessment result sets";
}

export function IntegrationsPage() {
  const { token, user } = useAuth();
  const [wazuhStatus, setWazuhStatus] = useState<WazuhIntegrationStatus | null>(null);
  const [suricataStatus, setSuricataStatus] = useState<SuricataIntegrationStatus | null>(null);
  const [nmapStatus, setNmapStatus] = useState<NmapIntegrationStatus | null>(null);
  const [hydraStatus, setHydraStatus] = useState<HydraIntegrationStatus | null>(null);
  const [activeImportTool, setActiveImportTool] = useState<ImportableTool | null>(null);
  const [isLoading, setIsLoading] = useState(true);
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
      fetchWazuhIntegrationStatus(token),
      fetchSuricataIntegrationStatus(token),
      fetchNmapIntegrationStatus(token),
      fetchHydraIntegrationStatus(token),
    ])
      .then(([wazuh, suricata, nmap, hydra]) => {
        if (!isActive) {
          return;
        }

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

  const statusLookup = {
    wazuh: wazuhStatus,
    suricata: suricataStatus,
    nmap: nmapStatus,
    hydra: hydraStatus,
  };

  const canImport = canImportPrimaryIntegrations(user?.role);

  return (
    <div className="space-y-6">
      <SectionCard
        title="Integration readiness"
        description="Track the four proposal-approved ingestion paths and import demo data for walkthroughs."
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

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {integrationCards.map((card) => {
            const status = statusLookup[card.tool];

            return (
              <div
                key={card.tool}
                className="rounded-[1.75rem] border border-brand-black/8 bg-white p-5 shadow-sm"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-light text-brand-orange">
                    <PlugIcon className="h-5 w-5" />
                  </div>
                  <StatusBadge variant={status?.status ?? "pending"}>
                    {status?.status ?? "pending"}
                  </StatusBadge>
                </div>

                <div className="mt-5">
                  <p className="text-lg font-semibold text-brand-black">{card.name}</p>
                  <p className="mt-1 text-sm text-brand-black/55">{card.vendor}</p>
                </div>

                <p className="mt-4 text-sm font-semibold text-brand-black">{card.title}</p>
                <p className="mt-2 text-sm leading-6 text-brand-black/70">{card.description}</p>

                {card.labOnly ? (
                  <div className="mt-4 flex flex-wrap gap-2">
                    <span className="rounded-full bg-brand-orange/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-brand-orange">
                      Authorized lab-only result ingestion
                    </span>
                    <span className="rounded-full bg-brand-black/5 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-brand-black/55">
                      No offensive automation
                    </span>
                  </div>
                ) : null}

                <div className="mt-5 rounded-[1.25rem] bg-brand-light/70 p-4">
                  <div className="space-y-3 text-sm text-brand-black/70">
                    <div className="flex justify-between gap-4">
                      <span>Imported alerts</span>
                      <span className="font-semibold text-brand-black">
                        {status?.imported_alert_count ?? 0}
                      </span>
                    </div>
                    <div className="flex justify-between gap-4">
                      <span>Imported logs</span>
                      <span className="font-semibold text-brand-black">
                        {status?.imported_log_count ?? 0}
                      </span>
                    </div>
                    <div className="flex justify-between gap-4">
                      <span>Last import</span>
                      <span className="font-semibold text-brand-black">
                        {formatDateTime(status?.last_import_at ?? null)}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="mt-5 space-y-3">
                  <button
                    type="button"
                    onClick={() => handleImportSampleData(card.tool)}
                    className="btn-primary w-full"
                    disabled={!canImport || activeImportTool !== null}
                  >
                    {activeImportTool === card.tool ? "Importing data..." : "Import sample data"}
                  </button>
                  <p className="text-xs leading-5 text-brand-black/55">
                    {canImport
                      ? `${status?.available_demo_payloads ?? 0} ${getImportPayloadLabel(card.tool)} are ready for guided imports.`
                      : "Viewer accounts can inspect status, but only admins and analysts can run imports."}
                  </p>
                  {status?.last_import_message ? (
                    <div className="rounded-[1.25rem] border border-brand-black/8 bg-brand-light/60 px-4 py-3 text-xs leading-5 text-brand-black/65">
                      {status.last_import_message}
                    </div>
                  ) : null}
                </div>
              </div>
            );
          })}
        </div>
      </SectionCard>

      <SectionCard
        title="Safety boundaries"
        description="The proposal scope stays defensive and presentation-friendly while still giving analysts live ingestion demos."
        tone="dark"
      >
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {integrationCards.map((card) => {
            const status = statusLookup[card.tool];

            return (
              <div
                key={`${card.tool}-latest`}
                className="rounded-[1.5rem] border border-brand-white/10 bg-brand-white/5 p-5"
              >
                <div className="flex items-center gap-3">
                  <ShieldIcon className="h-5 w-5 text-brand-orange" />
                  <p className="font-semibold text-white">{card.name}</p>
                </div>
                <p className="mt-3 text-sm leading-6 text-brand-muted">{card.description}</p>
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
    </div>
  );
}
