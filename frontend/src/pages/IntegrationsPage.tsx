import { PlugIcon, ShieldIcon } from "@/components/Icons";
import { SectionCard } from "@/components/SectionCard";
import { StatusBadge } from "@/components/StatusBadge";
import { integrations } from "@/data/mock";

export function IntegrationsPage() {
  return (
    <div className="space-y-6">
      <SectionCard
        title="Integration readiness"
        description="Monitor connection posture across core telemetry sources and safe lab-only ingestion workflows."
        eyebrow="Integrations"
        action={<button className="btn-primary">Add integration placeholder</button>}
      >
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {integrations.map((integration) => (
            <div
              key={integration.id}
              className="rounded-[1.75rem] border border-brand-black/8 bg-white p-5 shadow-sm"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-light text-brand-orange">
                  <PlugIcon className="h-5 w-5" />
                </div>
                <StatusBadge variant={integration.status}>{integration.status}</StatusBadge>
              </div>

              <div className="mt-5">
                <p className="text-lg font-semibold text-brand-black">{integration.name}</p>
                <p className="mt-1 text-sm text-brand-black/55">{integration.vendor}</p>
              </div>

              <p className="mt-4 text-sm leading-6 text-brand-black/70">{integration.description}</p>

              <div className="mt-5 rounded-[1.25rem] bg-brand-light/70 p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Last sync</p>
                <p className="mt-2 text-sm font-medium text-brand-black">{integration.lastSync}</p>
                {integration.note ? (
                  <p className="mt-3 text-xs font-semibold uppercase tracking-[0.18em] text-brand-orange">
                    {integration.note}
                  </p>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard
        title="Safety notes"
        description="Clear guardrails for classroom-facing integration coverage."
        tone="dark"
      >
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-[1.5rem] border border-brand-white/10 bg-brand-white/5 p-5">
            <div className="flex items-center gap-3">
              <ShieldIcon className="h-5 w-5 text-brand-orange" />
              <p className="font-semibold text-white">Nmap and Hydra remain lab-only</p>
            </div>
            <p className="mt-3 text-sm leading-6 text-brand-muted">
              Their cards and future parsers must remain limited to result ingestion, simulation,
              and visualization. No active offensive workflows should be added here.
            </p>
          </div>

          <div className="rounded-[1.5rem] border border-brand-white/10 bg-brand-white/5 p-5">
            <p className="font-semibold text-white">Preferred operational path</p>
            <p className="mt-3 text-sm leading-6 text-brand-muted">
              Wazuh and Suricata should remain the primary connected integrations for dashboard
              telemetry, incident creation, and alert-first analyst workflows.
            </p>
          </div>
        </div>
      </SectionCard>
    </div>
  );
}
