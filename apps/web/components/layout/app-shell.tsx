"use client";

import { useState } from "react";

import { Header } from "@/components/layout/header";
import { Sidebar } from "@/components/layout/sidebar";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="relative min-h-screen bg-[var(--background)] text-[var(--foreground)] lg:grid lg:grid-cols-[300px_minmax(0,1fr)]">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute inset-x-0 top-0 h-[360px] bg-[radial-gradient(circle_at_top_left,rgba(255,122,26,0.18),transparent_36%),radial-gradient(circle_at_top_right,rgba(17,17,17,0.08),transparent_24%)]" />
        <div className="absolute bottom-[-120px] right-[-80px] h-[320px] w-[320px] rounded-full bg-[rgba(255,122,26,0.08)] blur-3xl" />
      </div>
      <Sidebar mobileOpen={mobileOpen} onNavigate={() => setMobileOpen(false)} />
      <div className="relative min-h-screen">
        <Header onToggleSidebar={() => setMobileOpen((value) => !value)} />
        <main className="relative px-4 pb-8 pt-6 sm:px-6 lg:px-8">
          <div className="mx-auto w-full max-w-[1580px]">{children}</div>
        </main>
      </div>
    </div>
  );
}
