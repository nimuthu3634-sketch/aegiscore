"use client";

import { Bell, LogOut } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/format";
import { signOut, useAuth } from "@/hooks/use-auth";

export function Header({ title, lastRealtimeEvent }: { title: string; lastRealtimeEvent: Record<string, unknown> | null }) {
  const { data: user } = useAuth();

  return (
    <header className="flex flex-col gap-4 border-b bg-white/80 px-6 py-5 backdrop-blur lg:flex-row lg:items-center lg:justify-between">
      <div>
        <p className="text-xs uppercase tracking-[0.25em] text-[var(--muted)]">AegisCore workspace</p>
        <h1 className="mt-2 text-2xl font-semibold">{title}</h1>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        {lastRealtimeEvent && lastRealtimeEvent.event !== "connected" ? (
          <div className="flex items-center gap-2 rounded-2xl border bg-[#fff4eb] px-4 py-2 text-sm">
            <Bell className="h-4 w-4 text-[var(--accent)]" />
            <span>{String(lastRealtimeEvent.title)}</span>
            <Badge tone={String(lastRealtimeEvent.severity)}>{String(lastRealtimeEvent.severity)}</Badge>
          </div>
        ) : null}
        <div className="rounded-2xl border bg-white px-4 py-2 text-sm">
          <p className="font-semibold">{user?.full_name}</p>
          <p className="text-[var(--muted)]">
            {user?.role} {user?.last_login_at ? `• last login ${formatDate(user.last_login_at)}` : ""}
          </p>
        </div>
        <Button variant="outline" onClick={signOut}>
          <LogOut className="mr-2 h-4 w-4" />
          Sign out
        </Button>
      </div>
    </header>
  );
}
