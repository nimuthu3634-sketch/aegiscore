import { ContentCard } from "@/components/ContentCard";
import { PageHeader } from "@/components/PageHeader";

const roleCards = [
  {
    title: "Admin",
    detail: "Manage platform settings, integrations, roles, and environment configuration."
  },
  {
    title: "Analyst",
    detail: "Review alerts, investigate incidents, and generate reports."
  },
  {
    title: "Viewer",
    detail: "Read-only visibility for dashboards, reports, and presentation views."
  }
];

export function SettingsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Configuration"
        title="Settings"
        description="A starter configuration space for environment variables, user roles, and future admin controls."
        action={<button className="btn-primary">Save changes</button>}
      />

      <div className="grid gap-4 lg:grid-cols-3">
        {roleCards.map((role) => (
          <ContentCard key={role.title} title={role.title}>
            <p className="text-sm leading-6 text-brand-black/70">{role.detail}</p>
          </ContentCard>
        ))}
      </div>

      <ContentCard
        title="Environment placeholders"
        description="Scaffolded settings expected from env files and Docker Compose."
      >
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-[1.25rem] bg-brand-light p-4">
            <p className="text-sm font-semibold text-brand-black">Frontend</p>
            <p className="mt-2 font-mono text-xs text-brand-black/70">VITE_API_BASE_URL</p>
            <p className="mt-1 font-mono text-xs text-brand-black/70">VITE_WS_URL</p>
          </div>
          <div className="rounded-[1.25rem] bg-brand-light p-4">
            <p className="text-sm font-semibold text-brand-black">Backend</p>
            <p className="mt-2 font-mono text-xs text-brand-black/70">DATABASE_URL</p>
            <p className="mt-1 font-mono text-xs text-brand-black/70">REDIS_URL</p>
            <p className="mt-1 font-mono text-xs text-brand-black/70">SECRET_KEY</p>
          </div>
        </div>
      </ContentCard>
    </div>
  );
}
