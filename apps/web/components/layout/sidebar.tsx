"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, AlertTriangle, Bot, FileDown, LayoutDashboard, Logs, Network, Settings, Shield, UserCog, Users } from "lucide-react";

import { useAuth } from "@/hooks/use-auth";
import { cn } from "@/lib/utils";

const navigation = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/alerts", label: "Alerts", icon: AlertTriangle },
  { href: "/incidents", label: "Incidents", icon: Shield },
  { href: "/logs", label: "Logs", icon: Logs },
  { href: "/assets", label: "Assets", icon: Activity },
  { href: "/integrations", label: "Integrations", icon: Network },
  { href: "/ai", label: "AI Model", icon: Bot },
  { href: "/reports", label: "Reports", icon: FileDown },
  { href: "/profile", label: "Profile", icon: Users },
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/admin", label: "Admin", icon: UserCog },
];

export function Sidebar() {
  const pathname = usePathname();
  const { data: user } = useAuth();

  return (
    <aside className="hidden min-h-screen w-72 flex-col border-r border-[rgba(255,255,255,0.08)] bg-[#111111] px-5 py-6 text-white lg:flex">
      <div className="mb-8">
        <p className="text-xs uppercase tracking-[0.3em] text-[#ffb37f]">AegisCore</p>
        <h1 className="mt-3 text-2xl font-semibold">Defensive SOC</h1>
        <p className="mt-2 text-sm text-white/60">Analyst-first triage, incident response, and explainable AI prioritization.</p>
      </div>
      <nav className="space-y-2">
        {navigation
          .filter((item) => item.href !== "/admin" || user?.role === "Admin")
          .map((item) => {
          const Icon = item.icon;
          const active = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-2xl px-4 py-3 text-sm transition",
                active ? "bg-[#ff7a1a] text-white" : "text-white/70 hover:bg-white/10 hover:text-white",
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
