"use client";

import { Bell, LogOut, Menu } from "lucide-react";
import { usePathname } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAlertStream, useRealtimeStatus } from "@/hooks/use-alert-stream";
import { signOut, useAuth } from "@/hooks/use-auth";
import { formatDate } from "@/lib/format";

const routeLabels: Record<string, string> = {
  "/dashboard": "SOC Overview",
  "/alerts": "Alert Operations",
  "/incidents": "Incident Workflow",
  "/logs": "Log Explorer",
  "/assets": "Asset Visibility",
  "/integrations": "Telemetry Integrations",
  "/analytics": "Analytics & AI",
  "/reports": "Reporting",
  "/settings": "Settings",
  "/profile": "Profile",
  "/admin": "Admin Controls",
};

function resolveRouteLabel(pathname: string) {
  return Object.entries(routeLabels).find(([path]) => pathname.startsWith(path))?.[1] ?? "AegisCore";
}

export function Header({ onToggleSidebar }: { onToggleSidebar: () => void }) {
  const pathname = usePathname();
  const status = useRealtimeStatus();
  const lastEvent = useAlertStream();
  const { data: user } = useAuth();
  const routeLabel = resolveRouteLabel(pathname);

  return (
    <header className="sticky top-0 z-30 px-4 pt-4 sm:px-6 lg:px-8">
      <div className="rounded-[30px] border border-black/10 bg-[rgba(255,255,255,0.78)] shadow-[0_24px_54px_rgba(17,17,17,0.08)] backdrop-blur-xl">
        <div className="flex flex-col gap-5 px-5 py-5 xl:flex-row xl:items-center xl:justify-between xl:px-6">
          <div className="flex items-start gap-3">
            <Button variant="outline" size="icon" className="lg:hidden" onClick={onToggleSidebar}>
              <Menu className="h-4 w-4" />
            </Button>
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-3">
                <span className="inline-flex rounded-full border border-[#ffd2b2] bg-[var(--accent-soft)] px-3 py-1 text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-[#a54e10]">
                  Control layer
                </span>
                <span className="text-[11px] uppercase tracking-[0.3em] text-[#8a7d72]">AegisCore workspace</span>
              </div>
              <div>
                <h2 className="text-[1.65rem] font-semibold tracking-[-0.05em] text-[#111111]">{routeLabel}</h2>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-[#6d635a]">
                  Track defensive telemetry, analyst workload, and lab-safe imports from one polished operational surface.
                </p>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="rounded-[22px] border border-black/8 bg-white/70 px-4 py-3 text-sm shadow-[0_10px_28px_rgba(17,17,17,0.05)]">
              <p className="text-[11px] uppercase tracking-[0.24em] text-[#8a7d72]">Realtime</p>
              <div className="mt-2 flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-[var(--accent)]" />
                <Badge tone={status}>{status}</Badge>
              </div>
            </div>

            {lastEvent && lastEvent.event !== "connected" ? (
              <div className="hidden items-center gap-3 rounded-[22px] border border-[#ffd2b2] bg-[var(--accent-soft)] px-4 py-3 text-sm lg:flex">
                <Bell className="h-4 w-4 text-[var(--accent)]" />
                <div className="max-w-[240px]">
                  <p className="font-semibold text-[#111111]">{String(lastEvent.title ?? "New alert event")}</p>
                  <p className="text-xs uppercase tracking-[0.18em] text-[#8f5d34]">Operations update</p>
                </div>
                {"severity" in lastEvent ? <Badge tone={String(lastEvent.severity)}>{String(lastEvent.severity)}</Badge> : null}
              </div>
            ) : null}

            <div className="rounded-[22px] bg-[#111111] px-4 py-3 text-sm text-white shadow-[0_18px_36px_rgba(17,17,17,0.18)]">
              <p className="font-semibold">{user?.full_name ?? "Loading user"}</p>
              <p className="mt-1 text-white/62">
                {user?.role ?? "Unknown"}
                {user?.last_login_at ? ` | last login ${formatDate(user.last_login_at)}` : ""}
              </p>
            </div>

            <Button variant="outline" onClick={signOut}>
              <LogOut className="mr-2 h-4 w-4" />
              Sign out
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}
