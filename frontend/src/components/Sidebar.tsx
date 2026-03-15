import { NavLink } from "react-router-dom";

import logoUrl from "@repo-assets/aegiscore-logo.svg";

import { navigationItems } from "@/types/navigation";
import { classNames } from "@/utils/classNames";

type SidebarProps = {
  mobileOpen: boolean;
  onClose: () => void;
};

export function Sidebar({ mobileOpen, onClose }: SidebarProps) {
  return (
    <>
      <div
        className={classNames(
          "fixed inset-0 z-30 bg-brand-black/50 transition-opacity lg:hidden",
          mobileOpen ? "opacity-100" : "pointer-events-none opacity-0",
        )}
        onClick={onClose}
      />

      <aside
        className={classNames(
          "fixed inset-y-0 left-0 z-40 flex w-72 flex-col bg-brand-surface text-brand-white shadow-panel transition-transform duration-300 lg:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex items-center gap-3 border-b border-brand-white/10 px-6 py-5">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-white/10">
            <img src={logoUrl} alt="AegisCore logo" className="h-10 w-10 object-contain" />
          </div>
          <div>
            <p className="text-lg font-semibold">AegisCore</p>
            <p className="text-sm text-brand-muted">Lab SOC Console</p>
          </div>
        </div>

        <div className="px-6 py-5">
          <div className="rounded-2xl border border-brand-white/10 bg-brand-white/5 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-brand-muted">Operations</p>
            <p className="mt-2 text-sm leading-6 text-brand-muted">
              Defensive monitoring, incident handling, and explainable analytics for lab
              environments.
            </p>
          </div>
        </div>

        <nav className="flex-1 px-4">
          <ul className="space-y-1">
            {navigationItems.map((item) => (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  onClick={onClose}
                  className={({ isActive }) =>
                    classNames(
                      "group flex items-center justify-between rounded-2xl px-4 py-3 text-sm transition-colors",
                      isActive
                        ? "bg-brand-orange text-brand-white"
                        : "text-brand-muted hover:bg-brand-white/8 hover:text-brand-white",
                    )
                  }
                >
                  <div>
                    <p className="font-medium">{item.label}</p>
                    <p className="text-xs opacity-80">{item.description}</p>
                  </div>
                  <span className="rounded-full border border-current/20 px-2 py-0.5 text-[10px] uppercase tracking-[0.2em]">
                    SOC
                  </span>
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <div className="border-t border-brand-white/10 p-6">
          <div className="rounded-2xl bg-brand-white px-4 py-3 text-brand-black">
            <p className="text-xs uppercase tracking-[0.2em] text-brand-orange">Demo Access</p>
            <p className="mt-2 text-sm font-semibold">admin / analyst / viewer</p>
            <p className="mt-1 text-xs text-brand-black/70">
              JWT auth scaffold ready for backend wiring.
            </p>
          </div>
        </div>
      </aside>
    </>
  );
}
