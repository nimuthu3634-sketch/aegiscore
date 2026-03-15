import { useState } from "react";
import { Outlet } from "react-router-dom";

import { Sidebar } from "@/components/Sidebar";
import { TopNavbar } from "@/components/TopNavbar";

export function AppShell() {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <div className="min-h-screen bg-brand-light text-brand-black">
      <Sidebar mobileOpen={mobileNavOpen} onClose={() => setMobileNavOpen(false)} />

      <div className="min-h-screen lg:pl-72">
        <TopNavbar onMenuClick={() => setMobileNavOpen(true)} />

        <main className="px-4 pb-8 pt-4 sm:px-6 lg:px-8">
          <div className="soft-grid rounded-[2rem] p-3 sm:p-4">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
