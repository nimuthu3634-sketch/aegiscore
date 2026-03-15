import { useState } from "react";
import { Outlet } from "react-router-dom";

import { Header } from "@/components/Header";
import { LiveAlertToast } from "@/components/LiveAlertToast";
import { Sidebar } from "@/components/Sidebar";

export function AppShell() {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <div className="soc-background min-h-screen text-brand-black">
      <Sidebar mobileOpen={mobileNavOpen} onClose={() => setMobileNavOpen(false)} />
      <LiveAlertToast />

      <div className="min-h-screen lg:pl-72">
        <Header onMenuClick={() => setMobileNavOpen(true)} />

        <main className="px-4 pb-10 pt-5 sm:px-6 lg:px-8">
          <div className="ambient-grid rounded-[2.2rem] border border-white/60 bg-white/28 p-3 shadow-soft backdrop-blur-[2px] sm:p-4">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
