import { NavLink } from "react-router-dom";

import { BrandMark } from "@/components/BrandMark";
import {
  AlertTriangleIcon,
  DashboardIcon,
  IncidentIcon,
  LogIcon,
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
    logs: LogIcon,
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
          "fixed inset-y-0 left-0 z-40 flex w-72 flex-col overflow-hidden border-r border-brand-white/10 bg-brand-surface text-brand-white shadow-premium transition-transform duration-300 lg:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="pointer-events-none absolute -right-10 top-0 h-40 w-40 rounded-full bg-brand-orange/12 blur-3xl" />
        <div className="pointer-events-none absolute left-0 top-28 h-32 w-32 rounded-full bg-white/5 blur-3xl" />

        <div className="relative border-b border-brand-white/10 px-6 py-6">
          <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-brand-muted">
            Security platform
          </p>
          <BrandMark size="md" tone="dark" className="mt-4" />
          <p className="mt-4 text-sm text-brand-muted">Security Operations Center</p>
        </div>

        <div className="relative px-6 py-5">
          <div className="rounded-[1.6rem] border border-brand-white/10 bg-gradient-to-br from-brand-white/10 to-transparent p-5 backdrop-blur-sm">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-brand-orange/15 text-brand-orange">
                <ShieldIcon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.22em] text-brand-muted">Live posture</p>
                <p className="mt-1 text-sm font-semibold text-brand-white">Active monitoring</p>
              </div>
            </div>
            <p className="mt-3 text-sm leading-7 text-brand-muted">
              Monitor alerts, triage incidents, and manage security insights through a clean SOC
              workflow.
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
                        "group flex items-center justify-between rounded-[1.35rem] px-4 py-3 text-sm transition-all duration-200",
                        isActive
                          ? "bg-gradient-to-r from-brand-orange to-[#ff9d58] text-brand-white shadow-float"
                          : "text-brand-muted hover:bg-brand-white/7 hover:text-brand-white",
                      )
                    }
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-current/10">
                        <Icon className="h-5 w-5" />
                      </div>
                      <div>
                        <p className="font-medium">{item.label}</p>
                        <p className="text-xs leading-5 opacity-80">{item.description}</p>
                      </div>
                    </div>
                    <span className="h-2.5 w-2.5 rounded-full bg-current/70 transition group-hover:bg-brand-orange" />
                  </NavLink>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="relative border-t border-brand-white/10 p-6">
          <div className="rounded-[1.6rem] bg-white px-4 py-4 text-brand-black shadow-soft">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.22em] text-brand-orange">Access roles</p>
                <p className="mt-2 text-sm font-semibold">Admin, Analyst, Viewer</p>
              </div>
              <span className="rounded-full bg-emerald-100 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.12em] text-emerald-700">
                Ready
              </span>
            </div>
            <p className="mt-3 text-xs leading-6 text-brand-black/70">
              Auth, dashboard, alerts, incidents, logs, reports, integrations, and realtime
              updates are available across the workspace.
            </p>
          </div>
        </div>
      </aside>
    </>
  );
}
