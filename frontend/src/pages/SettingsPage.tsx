import { SectionCard } from "@/components/SectionCard";
import { accountSettings, brandingSettings, systemConfig } from "@/data/mock";

export function SettingsPage() {
  return (
    <div className="space-y-6">
      <SectionCard
        title="Settings and brand controls"
        description="Presentation-ready configuration panels for branding, account placeholders, and future system controls."
        eyebrow="Settings"
        action={<button className="btn-primary">Save placeholder</button>}
      >
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Theme mode</p>
            <p className="mt-3 text-lg font-semibold text-brand-black">SOC Light</p>
            <p className="mt-2 text-sm text-brand-black/60">
              Dark navigation, light workspace, orange accents.
            </p>
          </div>
          <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Logo source</p>
            <p className="mt-3 text-lg font-semibold text-brand-black">assets/aegiscore-logo.svg</p>
            <p className="mt-2 text-sm text-brand-black/60">Shared across login, header, and sidebar.</p>
          </div>
          <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Status</p>
            <p className="mt-3 text-lg font-semibold text-brand-black">Frontend-only mock state</p>
            <p className="mt-2 text-sm text-brand-black/60">No backend calls are wired yet.</p>
          </div>
        </div>
      </SectionCard>

      <div className="grid gap-6 xl:grid-cols-3">
        <SectionCard title="Theme and branding" description="Core palette and UI identity settings.">
          <div className="space-y-4">
            {brandingSettings.map((item) => (
              <div key={item.label} className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
                <div className="flex items-center justify-between gap-4">
                  <p className="font-semibold text-brand-black">{item.label}</p>
                  <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-brand-black">
                    {item.value}
                  </span>
                </div>
                <p className="mt-3 text-sm leading-6 text-brand-black/65">{item.description}</p>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Account" description="Current presentation-session identity placeholders.">
          <div className="space-y-4">
            {accountSettings.map((item) => (
              <div key={item.label} className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">{item.label}</p>
                <p className="mt-2 text-lg font-semibold text-brand-black">{item.value}</p>
                <p className="mt-2 text-sm leading-6 text-brand-black/65">{item.description}</p>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="System config" description="Placeholder switches and environment settings.">
          <div className="space-y-4">
            {systemConfig.map((item) => (
              <div key={item.label} className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
                <div className="flex items-center justify-between gap-4">
                  <p className="font-semibold text-brand-black">{item.label}</p>
                  <button
                    type="button"
                    className="inline-flex h-7 w-12 rounded-full bg-brand-orange/20 p-1"
                  >
                    <span className="h-5 w-5 rounded-full bg-brand-orange" />
                  </button>
                </div>
                <p className="mt-2 text-sm font-medium text-brand-black">{item.value}</p>
                <p className="mt-2 text-sm leading-6 text-brand-black/65">{item.description}</p>
              </div>
            ))}
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
