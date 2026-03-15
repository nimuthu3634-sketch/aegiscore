import { Link } from "react-router-dom";

import logoUrl from "@repo-assets/aegiscore-logo.svg";

import { ArrowRightIcon, ShieldIcon, UserIcon } from "@/components/Icons";
import { StatusBadge } from "@/components/StatusBadge";

export function LoginPage() {
  return (
    <div className="soc-background min-h-screen px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-7xl items-center">
        <div className="grid w-full gap-6 lg:grid-cols-[1.15fr_0.85fr]">
          <section className="rounded-[2.25rem] bg-brand-surface p-8 text-white shadow-panel sm:p-10 lg:p-12">
            <div className="flex items-center gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-3xl bg-brand-orange shadow-lg shadow-brand-orange/20">
                <img src={logoUrl} alt="AegisCore logo" className="h-11 w-11 object-contain" />
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.3em] text-brand-muted">
                  AI-integrated SOC
                </p>
                <h1 className="mt-2 text-4xl font-semibold tracking-tight sm:text-5xl">
                  AegisCore
                </h1>
              </div>
            </div>

            <p className="mt-8 max-w-2xl text-lg leading-8 text-brand-muted">
              A polished Security Operations Center dashboard for lab-based monitoring, incident
              handling, and presentation-ready cybersecurity reporting.
            </p>

            <div className="mt-10 grid gap-4 sm:grid-cols-3">
              {[
                { title: "Admin", detail: "Controls integrations and oversight." },
                { title: "Analyst", detail: "Works alerts and incident queues." },
                { title: "Viewer", detail: "Observes reports and outcomes." },
              ].map((role) => (
                <div
                  key={role.title}
                  className="rounded-[1.5rem] border border-brand-white/10 bg-brand-white/5 p-4"
                >
                  <p className="text-sm font-semibold text-white">{role.title}</p>
                  <p className="mt-2 text-sm leading-6 text-brand-muted">{role.detail}</p>
                </div>
              ))}
            </div>

            <div className="mt-10 grid gap-4 md:grid-cols-2">
              <div className="rounded-[1.5rem] border border-brand-white/10 bg-brand-white/5 p-5">
                <div className="flex items-center gap-3">
                  <ShieldIcon className="h-5 w-5 text-brand-orange" />
                  <p className="font-semibold text-white">Lab-safe workflow</p>
                </div>
                <p className="mt-3 text-sm leading-6 text-brand-muted">
                  Supports Wazuh and Suricata monitoring plus safe classroom ingestion for Nmap and
                  Hydra result files.
                </p>
              </div>
              <div className="rounded-[1.5rem] border border-brand-white/10 bg-brand-white/5 p-5">
                <div className="flex items-center gap-3">
                  <UserIcon className="h-5 w-5 text-brand-orange" />
                  <p className="font-semibold text-white">Presentation-ready layout</p>
                </div>
                <p className="mt-3 text-sm leading-6 text-brand-muted">
                  Branded sidebar, executive dashboard cards, clean tables, and drill-down panels.
                </p>
              </div>
            </div>
          </section>

          <section className="panel rounded-[2.25rem] p-8 sm:p-10">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-brand-orange">
                  Sign in
                </p>
                <h2 className="mt-2 text-3xl font-semibold text-brand-black">Access the SOC</h2>
              </div>
              <StatusBadge variant="ready">demo mode</StatusBadge>
            </div>

            <p className="mt-4 text-sm leading-6 text-brand-black/65">
              This frontend remains disconnected from the backend. Use the placeholder form and
              continue into the dashboard shell for the presentation-ready UI.
            </p>

            <form className="mt-8 space-y-5">
              <label className="block text-sm font-medium text-brand-black">
                Email
                <input
                  type="email"
                  placeholder="analyst@aegiscore.local"
                  className="input-shell mt-2 w-full bg-brand-light outline-none placeholder:text-brand-black/35"
                />
              </label>

              <label className="block text-sm font-medium text-brand-black">
                Password
                <input
                  type="password"
                  placeholder="Enter password"
                  className="input-shell mt-2 w-full bg-brand-light outline-none placeholder:text-brand-black/35"
                />
              </label>

              <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
                <p className="text-sm font-semibold text-brand-black">Demo credentials</p>
                <ul className="mt-3 space-y-2 text-sm text-brand-black/65">
                  <li>admin@aegiscore.local / admin123</li>
                  <li>analyst@aegiscore.local / analyst123</li>
                  <li>viewer@aegiscore.local / viewer123</li>
                </ul>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <Link to="/dashboard" className="btn-primary inline-flex items-center justify-center gap-2">
                  Continue
                  <ArrowRightIcon className="h-4 w-4" />
                </Link>
                <button type="button" className="btn-secondary">
                  Forgot password
                </button>
              </div>
            </form>
          </section>
        </div>
      </div>
    </div>
  );
}
