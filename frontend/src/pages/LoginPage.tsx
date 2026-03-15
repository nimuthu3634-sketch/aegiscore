import { useMemo, useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import logoUrl from "@repo-assets/aegiscore-logo.svg";

import { ArrowRightIcon, ShieldIcon, UserIcon } from "@/components/Icons";
import { useAuth } from "@/hooks/useAuth";
import { StatusBadge } from "@/components/StatusBadge";
import type { UserRole } from "@/types/auth";

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, register, isLoading } = useAuth();

  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("analyst@aegiscore.local");
  const [password, setPassword] = useState("password");
  const [fullName, setFullName] = useState("AegisCore Analyst");
  const [role, setRole] = useState<UserRole>("analyst");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const redirectPath = useMemo(() => {
    const nextPath = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
    return nextPath ?? "/dashboard";
  }, [location.state]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      if (mode === "login") {
        await login({ email, password });
      } else {
        await register({ full_name: fullName, email, password, role });
      }

      navigate(redirectPath, { replace: true });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Authentication failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

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
              Sign in with seeded demo credentials or create a new local demo account through the
              backend auth scaffold.
            </p>

            <div className="mt-8 inline-flex rounded-full bg-brand-light p-1">
              <button
                type="button"
                onClick={() => setMode("login")}
                className={`rounded-full px-4 py-2 text-sm font-semibold ${mode === "login" ? "bg-brand-orange text-white" : "text-brand-black/65"}`}
              >
                Login
              </button>
              <button
                type="button"
                onClick={() => setMode("register")}
                className={`rounded-full px-4 py-2 text-sm font-semibold ${mode === "register" ? "bg-brand-orange text-white" : "text-brand-black/65"}`}
              >
                Register
              </button>
            </div>

            <form className="mt-6 space-y-5" onSubmit={handleSubmit}>
              {mode === "register" ? (
                <label className="block text-sm font-medium text-brand-black">
                  Full name
                  <input
                    type="text"
                    value={fullName}
                    onChange={(event) => setFullName(event.target.value)}
                    placeholder="Your full name"
                    className="input-shell mt-2 w-full bg-brand-light outline-none placeholder:text-brand-black/35"
                  />
                </label>
              ) : null}

              <label className="block text-sm font-medium text-brand-black">
                Email
                <input
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="analyst@aegiscore.local"
                  className="input-shell mt-2 w-full bg-brand-light outline-none placeholder:text-brand-black/35"
                />
              </label>

              <label className="block text-sm font-medium text-brand-black">
                Password
                <input
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Enter password"
                  className="input-shell mt-2 w-full bg-brand-light outline-none placeholder:text-brand-black/35"
                />
              </label>

              {mode === "register" ? (
                <label className="block text-sm font-medium text-brand-black">
                  Role
                  <select
                    value={role}
                    onChange={(event) => setRole(event.target.value as UserRole)}
                    className="input-shell mt-2 w-full bg-brand-light outline-none"
                  >
                    <option value="admin">Admin</option>
                    <option value="analyst">Analyst</option>
                    <option value="viewer">Viewer</option>
                  </select>
                </label>
              ) : null}

              <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 p-4">
                <p className="text-sm font-semibold text-brand-black">Demo credentials</p>
                <ul className="mt-3 space-y-2 text-sm text-brand-black/65">
                  <li>admin@aegiscore.local / password</li>
                  <li>analyst@aegiscore.local / password</li>
                  <li>viewer@aegiscore.local / password</li>
                </ul>
              </div>

              {errorMessage ? (
                <div className="rounded-[1.5rem] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  {errorMessage}
                </div>
              ) : null}

              <div className="grid gap-3 sm:grid-cols-2">
                <button
                  type="submit"
                  disabled={isSubmitting || isLoading}
                  className="btn-primary inline-flex items-center justify-center gap-2 disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {isSubmitting ? "Please wait" : mode === "login" ? "Sign in" : "Create account"}
                  <ArrowRightIcon className="h-4 w-4" />
                </button>
                <button type="button" className="btn-secondary">
                  Demo mode active
                </button>
              </div>
            </form>
          </section>
        </div>
      </div>
    </div>
  );
}
