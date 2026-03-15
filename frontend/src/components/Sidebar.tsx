import { NavLink } from "react-router-dom";

import logoUrl from "@repo-assets/aegiscore-logo.svg";

import {
  AlertTriangleIcon,
  DashboardIcon,
  IncidentIcon,
  PlugIcon,
  ReportIcon,
  SettingsIcon,
  ShieldIcon,
} from "@/components/Icons";
import { navigationItems } from "@/types/navigation";
import { classNames } from "@/utils/classNames";

type SidebarProps = {
  mobileOpen: boolean;
  onClose: () => void;
};

export function Sidebar({ mobileOpen, onClose }: SidebarProps) {
  const navIcons = {
    dashboard: DashboardIcon,
    alerts: AlertTriangleIcon,
    incidents: IncidentIcon,
    reports: ReportIcon,
    integrations: PlugIcon,
    settings: SettingsIcon,
  } as const;

  return (
    <>
      <div
        className={classNames(
          "fixed inset-0 z-30 bg-brand-black/60 transition-opacity lg:hidden",
          mobileOpen ? "opacity-100" : "pointer-events-none opacity-0",
        )}
        onClick={onClose}
      />

      <aside
        className={classNames(
          "fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-brand-white/10 bg-brand-surface text-brand-white shadow-panel transition-transform duration-300 lg:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex items-center gap-3 border-b border-brand-white/10 px-6 py-6">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-orange to-[#ff9a53] shadow-lg shadow-brand-orange/20">
            <img src={logoUrl} alt="AegisCore logo" className="h-10 w-10 object-contain" />
          </div>
          <div>
            <p className="text-lg font-semibold">AegisCore</p>
            <p className="text-sm text-brand-muted">Security Operations Center</p>
          </div>
        </div>

        <div className="px-6 py-5">
          <div className="rounded-[1.5rem] border border-brand-white/10 bg-gradient-to-br from-brand-white/8 to-transparent p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-brand-orange/15 text-brand-orange">
                <ShieldIcon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-brand-muted">Live posture</p>
                <p className="mt-1 text-sm font-semibold text-brand-white">Defensive lab mode</p>
              </div>
            </div>
            <p className="mt-3 text-sm leading-6 text-brand-muted">
              Monitor alerts, triage incidents, and present lab-only security insights with a
              clean SOC workflow.
            </p>
          </div>
        </div>

        <nav className="flex-1 px-4">
          <ul className="space-y-1">
            {navigationItems.map((item) => {
              const Icon = navIcons[item.icon];

              return (
                <li key={item.path}>
                  <NavLink
                    to={item.path}
                    onClick={onClose}
                    className={({ isActive }) =>
                      classNames(
                        "group flex items-center justify-between rounded-[1.25rem] px-4 py-3 text-sm transition-all",
                        isActive
                          ? "bg-brand-orange text-brand-white shadow-lg shadow-brand-orange/20"
                          : "text-brand-muted hover:bg-brand-white/8 hover:text-brand-white",
                      )
                    }
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-current/10">
                        <Icon className="h-5 w-5" />
                      </div>
                      <div>
                        <p className="font-medium">{item.label}</p>
                        <p className="text-xs opacity-80">{item.description}</p>
                      </div>
                    </div>
                    <span className="rounded-full border border-current/20 px-2 py-0.5 text-[10px] uppercase tracking-[0.2em]">
                      View
                    </span>
                  </NavLink>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="border-t border-brand-white/10 p-6">
          <div className="rounded-[1.5rem] bg-white px-4 py-4 text-brand-black">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-brand-orange">Demo roles</p>
                <p className="mt-2 text-sm font-semibold">Admin, Analyst, Viewer</p>
              </div>
              <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
                Ready
              </span>
            </div>
            <p className="mt-3 text-xs leading-5 text-brand-black/70">
              Auth is live for demo access. Dashboard and workflow data still use student-friendly
              mock content for presentation flow.
            </p>
          </div>
        </div>
      </aside>
    </>
  );
}
