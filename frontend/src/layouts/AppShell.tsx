import { useState } from "react";
import { Outlet } from "react-router-dom";

import { Header } from "@/components/Header";
import { Sidebar } from "@/components/Sidebar";

export function AppShell() {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <div className="soc-background min-h-screen text-brand-black">
      <Sidebar mobileOpen={mobileNavOpen} onClose={() => setMobileNavOpen(false)} />

      <div className="min-h-screen lg:pl-72">
        <Header onMenuClick={() => setMobileNavOpen(true)} />

        <main className="px-4 pb-8 pt-4 sm:px-6 lg:px-8">
          <div className="ambient-grid rounded-[2rem] p-3 sm:p-4">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
