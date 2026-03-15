import { Link } from "react-router-dom";

import logoUrl from "@repo-assets/aegiscore-logo.svg";

export function LoginPage() {
  return (
    <div className="min-h-screen bg-brand-light px-4 py-10 sm:px-6 lg:px-8">
      <div className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-6xl items-center">
        <div className="grid w-full gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <section className="rounded-[2rem] bg-brand-surface p-8 text-brand-white shadow-panel sm:p-12">
            <div className="flex items-center gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-3xl bg-brand-white/10">
                <img src={logoUrl} alt="AegisCore logo" className="h-12 w-12 object-contain" />
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-brand-muted">
                  AI-integrated SOC
                </p>
                <h1 className="mt-2 text-4xl font-semibold">AegisCore</h1>
              </div>
            </div>

            <p className="mt-8 max-w-2xl text-lg leading-8 text-brand-muted">
              A clean Security Operations Center workspace for lab-based monitoring, alert triage,
              incident management, and explainable anomaly detection.
            </p>

            <div className="mt-10 grid gap-4 sm:grid-cols-3">
              {[
                { label: "Admin", detail: "Configuration and approvals" },
                { label: "Analyst", detail: "Triage and investigations" },
                { label: "Viewer", detail: "Read-only oversight" }
              ].map((role) => (
                <div
                  key={role.label}
                  className="rounded-[1.5rem] border border-brand-white/10 bg-brand-white/5 p-4"
                >
                  <p className="text-sm font-semibold text-brand-white">{role.label}</p>
                  <p className="mt-2 text-sm text-brand-muted">{role.detail}</p>
                </div>
              ))}
            </div>

            <div className="mt-10 flex flex-wrap gap-3">
              <Link to="/dashboard" className="btn-primary">
                Enter dashboard
              </Link>
              <button
                type="button"
                className="btn-secondary border-brand-white/15 bg-brand-white/10 text-brand-white hover:bg-brand-white/15"
              >
                Demo credentials
              </button>
            </div>
          </section>

          <section className="rounded-[2rem] bg-white p-8 shadow-panel sm:p-10">
            <p className="text-xs uppercase tracking-[0.24em] text-brand-orange">Sign in</p>
            <h2 className="mt-2 text-2xl font-semibold text-brand-black">Analyst access panel</h2>
            <p className="mt-2 text-sm leading-6 text-brand-black/65">
              Authentication is scaffolded for JWT role-based flows. Business logic can be wired in
              without changing the app structure.
            </p>

            <form className="mt-8 space-y-4">
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-brand-black">Email</span>
                <input
                  type="email"
                  placeholder="analyst@aegiscore.local"
                  className="w-full rounded-2xl border border-brand-black/10 bg-brand-light px-4 py-3 outline-none ring-0 transition focus:border-brand-orange"
                />
              </label>

              <label className="block">
                <span className="mb-2 block text-sm font-medium text-brand-black">Password</span>
                <input
                  type="password"
                  placeholder="Enter password"
                  className="w-full rounded-2xl border border-brand-black/10 bg-brand-light px-4 py-3 outline-none ring-0 transition focus:border-brand-orange"
                />
              </label>

              <div className="rounded-2xl bg-brand-light p-4 text-sm text-brand-black/65">
                Starter roles: <strong>admin</strong>, <strong>analyst</strong>, and{" "}
                <strong>viewer</strong>.
              </div>

              <div className="flex flex-wrap gap-3 pt-2">
                <Link to="/dashboard" className="btn-primary">
                  Continue
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
