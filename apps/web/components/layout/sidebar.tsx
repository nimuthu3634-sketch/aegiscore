"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  AlertTriangle,
  Bot,
  FileDown,
  LayoutDashboard,
  Logs,
  Network,
  Settings,
  Shield,
  UserCog,
  UserRound,
  X,
} from "lucide-react";

import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { cn } from "@/lib/utils";

const navigation = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/alerts", label: "Alerts", icon: AlertTriangle },
  { href: "/incidents", label: "Incidents", icon: Shield },
  { href: "/logs", label: "Logs Explorer", icon: Logs },
  { href: "/assets", label: "Assets", icon: Activity },
  { href: "/integrations", label: "Integrations", icon: Network },
  { href: "/analytics", label: "Analytics", icon: Bot },
  { href: "/reports", label: "Reports", icon: FileDown },
  { href: "/profile", label: "Profile", icon: UserRound },
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/admin", label: "Admin / Users", icon: UserCog },
];

const secondaryRoutes = new Set(["/profile", "/settings", "/admin"]);

export function Sidebar({
  mobileOpen,
  onNavigate,
}: {
  mobileOpen: boolean;
  onNavigate: () => void;
}) {
  const pathname = usePathname();
  const { data: user } = useAuth();
  const visibleNavigation = navigation.filter((item) => item.href !== "/admin" || user?.role === "Admin");
  const operations = visibleNavigation.filter((item) => !secondaryRoutes.has(item.href));
  const account = visibleNavigation.filter((item) => secondaryRoutes.has(item.href));

  return (
    <>
      <div className={cn("fixed inset-0 z-40 bg-[#111111]/40 lg:hidden", mobileOpen ? "block" : "hidden")} onClick={onNavigate} />
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-[300px] flex-col overflow-hidden border-r border-white/10 bg-[#111111] px-5 py-5 text-white transition-transform duration-300 lg:sticky lg:top-0 lg:z-auto lg:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_0%_12%,rgba(255,122,26,0.26),transparent_28%),linear-gradient(180deg,#171311_0%,#111111_54%,#0d0b0a_100%)]" />
        <div className="absolute left-[-56px] top-[160px] h-[180px] w-[180px] rounded-full bg-[rgba(255,122,26,0.16)] blur-3xl" />
        <div className="relative flex h-full flex-col">
          <div className="flex items-start justify-between gap-3">
            <div>
              <Logo href="/dashboard" tone="light" />
              <p className="mt-4 text-[11px] uppercase tracking-[0.32em] text-white/42">Local deployment mode</p>
            </div>
            <Button variant="ghost" size="icon" className="text-white lg:hidden" onClick={onNavigate}>
              <X className="h-5 w-5" />
            </Button>
          </div>

          <div className="mt-6 rounded-[28px] border border-white/10 bg-white/[0.05] p-5 shadow-[0_22px_42px_rgba(0,0,0,0.18)]">
            <p className="text-[11px] uppercase tracking-[0.32em] text-[#ffb37f]">Command posture</p>
            <h2 className="mt-3 text-lg font-semibold tracking-[-0.03em] text-white">Calm operations for noisy defensive telemetry.</h2>
            <p className="mt-3 text-sm leading-6 text-white/68">
              AegisCore keeps analysts inside a lab-safe, explainable workspace for triage, incidents, and import-only telemetry review.
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              {["Lab-safe only", "Demo ready", "Orange response rail"].map((label) => (
                <span key={label} className="rounded-full border border-white/12 bg-white/[0.03] px-3 py-1 text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-white/70">
                  {label}
                </span>
              ))}
            </div>
          </div>

          <div className="mt-8 flex-1 space-y-7 overflow-y-auto pr-1">
            <div className="space-y-2">
              <p className="text-[11px] uppercase tracking-[0.28em] text-white/38">Operations</p>
              <nav className="space-y-2">
                {operations.map((item) => {
                  const active = pathname.startsWith(item.href);
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={onNavigate}
                      className={cn(
                        "flex items-center gap-3 rounded-[22px] border px-4 py-3 text-sm transition",
                        active
                          ? "border-[#ff8d40] bg-[linear-gradient(135deg,rgba(255,122,26,0.24),rgba(255,122,26,0.12))] text-white shadow-[0_16px_32px_rgba(255,122,26,0.18)]"
                          : "border-transparent text-white/68 hover:border-white/10 hover:bg-white/[0.04] hover:text-white",
                      )}
                    >
                      <span className={cn("flex h-9 w-9 items-center justify-center rounded-2xl", active ? "bg-white/12" : "bg-white/[0.04]")}>
                        <Icon className="h-4 w-4" />
                      </span>
                      <span className="flex-1">{item.label}</span>
                    </Link>
                  );
                })}
              </nav>
            </div>

            <div className="space-y-2">
              <p className="text-[11px] uppercase tracking-[0.28em] text-white/38">Account</p>
              <nav className="space-y-2">
                {account.map((item) => {
                  const active = pathname.startsWith(item.href);
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={onNavigate}
                      className={cn(
                        "flex items-center gap-3 rounded-[22px] border px-4 py-3 text-sm transition",
                        active
                          ? "border-[#ff8d40] bg-[linear-gradient(135deg,rgba(255,122,26,0.24),rgba(255,122,26,0.12))] text-white shadow-[0_16px_32px_rgba(255,122,26,0.18)]"
                          : "border-transparent text-white/68 hover:border-white/10 hover:bg-white/[0.04] hover:text-white",
                      )}
                    >
                      <span className={cn("flex h-9 w-9 items-center justify-center rounded-2xl", active ? "bg-white/12" : "bg-white/[0.04]")}>
                        <Icon className="h-4 w-4" />
                      </span>
                      <span className="flex-1">{item.label}</span>
                    </Link>
                  );
                })}
              </nav>
            </div>
          </div>

          <div className="mt-6 rounded-[28px] border border-white/10 bg-[#0f0d0c]/70 p-5 shadow-[0_24px_44px_rgba(0,0,0,0.2)]">
            <p className="text-[11px] uppercase tracking-[0.3em] text-white/42">Operator</p>
            <div className="mt-3 rounded-[22px] border border-white/10 bg-white/[0.05] p-4">
              <p className="font-semibold text-white">{user?.full_name ?? "Analyst"}</p>
              <p className="mt-1 text-sm text-white/60">{user?.role ?? "Loading..."}</p>
            </div>
            <div className="mt-4 grid gap-3">
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-3">
                <p className="text-[11px] uppercase tracking-[0.24em] text-white/38">Telemetry scope</p>
                <p className="mt-2 text-sm text-white/72">Wazuh, Suricata, and lab-only Nmap/Hydra imports.</p>
              </div>
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-3">
                <p className="text-[11px] uppercase tracking-[0.24em] text-white/38">Presentation mode</p>
                <p className="mt-2 text-sm text-white/72">Built for walkthroughs, lecturer demos, and explainable analyst flow.</p>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
