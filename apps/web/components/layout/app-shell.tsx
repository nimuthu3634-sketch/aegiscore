"use client";

import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { useAlertStream } from "@/hooks/use-alert-stream";

export function AppShell({ title, children }: { title: string; children: React.ReactNode }) {
  const lastEvent = useAlertStream();

  return (
    <div className="min-h-screen lg:flex">
      <Sidebar />
      <div className="flex min-h-screen flex-1 flex-col">
        <Header title={title} lastRealtimeEvent={lastEvent} />
        <main className="flex-1 px-4 py-6 lg:px-6">{children}</main>
      </div>
    </div>
  );
}
