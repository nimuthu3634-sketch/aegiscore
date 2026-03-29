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

  return (
    <header className="sticky top-0 z-30 border-b border-[var(--border)] bg-white/90 backdrop-blur">
      <div className="flex flex-col gap-4 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
        <div className="flex items-start gap-3">
          <Button variant="outline" size="icon" className="lg:hidden" onClick={onToggleSidebar}>
            <Menu className="h-4 w-4" />
          </Button>
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-[#8f8f8f]">AegisCore workspace</p>
            <h2 className="mt-2 text-xl font-semibold tracking-[-0.03em] text-[#111111]">{resolveRouteLabel(pathname)}</h2>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 rounded-full border bg-[#fcfcfc] px-3 py-2 text-sm">
            <span className="h-2 w-2 rounded-full bg-[#FF7A1A]" />
            <span className="text-[#6f6f6f]">Realtime</span>
            <Badge tone={status}>{status}</Badge>
          </div>

          {lastEvent && lastEvent.event !== "connected" ? (
            <div className="hidden items-center gap-2 rounded-full border bg-[#fff4eb] px-4 py-2 text-sm lg:flex">
              <Bell className="h-4 w-4 text-[#FF7A1A]" />
              <span className="max-w-[220px] truncate font-medium text-[#111111]">{String(lastEvent.title ?? "New alert event")}</span>
              {"severity" in lastEvent ? <Badge tone={String(lastEvent.severity)}>{String(lastEvent.severity)}</Badge> : null}
            </div>
          ) : null}

          <div className="rounded-full border bg-white px-4 py-2 text-sm">
            <p className="font-semibold text-[#111111]">{user?.full_name ?? "Loading user"}</p>
            <p className="text-[#6f6f6f]">
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
    </header>
  );
}
