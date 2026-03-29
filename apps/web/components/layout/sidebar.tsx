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

export function Sidebar({
  mobileOpen,
  onNavigate,
}: {
  mobileOpen: boolean;
  onNavigate: () => void;
}) {
  const pathname = usePathname();
  const { data: user } = useAuth();

  return (
    <>
      <div className={cn("fixed inset-0 z-40 bg-[#111111]/40 lg:hidden", mobileOpen ? "block" : "hidden")} onClick={onNavigate} />
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-[280px] flex-col border-r border-white/10 bg-[#111111] px-5 py-5 text-white transition-transform duration-300 lg:sticky lg:top-0 lg:z-auto lg:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex items-start justify-between gap-3">
          <Logo href="/dashboard" />
          <Button variant="ghost" size="icon" className="text-white lg:hidden" onClick={onNavigate}>
            <X className="h-5 w-5" />
          </Button>
        </div>

        <div className="mt-8 rounded-[1.5rem] border border-white/10 bg-white/5 p-4">
          <p className="text-xs uppercase tracking-[0.28em] text-[#ffb37f]">Mission</p>
          <p className="mt-3 text-sm leading-6 text-white/78">
            Defensive telemetry, explainable risk scoring, and analyst workflows designed for small and medium SOC teams.
          </p>
        </div>

        <nav className="mt-8 space-y-1.5">
          {navigation
            .filter((item) => item.href !== "/admin" || user?.role === "Admin")
            .map((item) => {
              const active = pathname.startsWith(item.href);
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onNavigate}
                  className={cn(
                    "flex items-center gap-3 rounded-2xl px-4 py-3 text-sm transition",
                    active ? "bg-[#FF7A1A] text-white shadow-[0_14px_28px_rgba(255,122,26,0.25)]" : "text-white/72 hover:bg-white/8 hover:text-white",
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
        </nav>

        <div className="mt-auto rounded-[1.5rem] border border-white/10 bg-white/5 p-4">
          <p className="text-xs uppercase tracking-[0.24em] text-white/50">Signed in as</p>
          <p className="mt-3 font-semibold">{user?.full_name ?? "Analyst"}</p>
          <p className="mt-1 text-sm text-white/60">{user?.role ?? "Loading..."}</p>
        </div>
      </aside>
    </>
  );
}
