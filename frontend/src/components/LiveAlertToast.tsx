import { AlertTriangleIcon } from "@/components/Icons";
import { SeverityBadge } from "@/components/SeverityBadge";
import { useRealtime } from "@/hooks/useRealtime";

const toolLabels = {
  wazuh: "Wazuh",
  suricata: "Suricata",
  nmap: "Nmap",
  hydra: "Hydra",
  virtualbox: "VirtualBox",
};

export function LiveAlertToast() {
  const { liveAlertToast, dismissLiveAlertToast } = useRealtime();

  if (!liveAlertToast) {
    return null;
  }

  const { count, latestAlert } = liveAlertToast;
  const toolLabel = toolLabels[latestAlert.source_tool];

  return (
    <div className="pointer-events-none fixed right-4 top-24 z-50 w-full max-w-sm sm:right-6 lg:right-8">
      <div className="pointer-events-auto overflow-hidden rounded-[1.5rem] border border-brand-orange/25 bg-brand-surface text-white shadow-2xl">
        <div className="h-1.5 bg-brand-orange" />
        <div className="p-4">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-brand-orange text-white">
              <AlertTriangleIcon className="h-5 w-5" />
            </div>

            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-semibold text-white">
                  {count > 1 ? `${count} live alerts received` : "Live alert received"}
                </p>
                <button
                  type="button"
                  onClick={dismissLiveAlertToast}
                  className="rounded-full bg-white/5 px-2 py-1 text-xs font-semibold text-brand-muted transition hover:bg-white/10 hover:text-white"
                >
                  Dismiss
                </button>
              </div>

              <p className="mt-2 truncate text-sm font-medium text-white">{latestAlert.title}</p>
              <p className="mt-1 text-xs leading-5 text-brand-muted">
                {toolLabel} on {latestAlert.source}
              </p>

              <div className="mt-3 flex flex-wrap items-center gap-2">
                <SeverityBadge level={latestAlert.severity} />
                <span className="rounded-full bg-white/5 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-brand-muted">
                  auto-refresh queued
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
