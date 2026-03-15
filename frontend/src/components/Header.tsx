import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useLocation } from "react-router-dom";

import logoUrl from "@repo-assets/aegiscore-logo.svg";

import { BellIcon, ChevronDownIcon, MenuIcon, SearchIcon } from "@/components/Icons";
import { useAuth } from "@/hooks/useAuth";
import { navigationItems } from "@/types/navigation";

type HeaderProps = {
  onMenuClick: () => void;
};

const pageLookup = new Map(navigationItems.map((item) => [item.path, item]));

export function Header({ onMenuClick }: HeaderProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const page = pageLookup.get(location.pathname);
  const pageTitle = page?.label ?? "AegisCore";
  const pageDescription = page?.description ?? "Security operations workspace";
  const roleLabel = useMemo(() => {
    if (!user) {
      return "Guest";
    }

    return user.role.charAt(0).toUpperCase() + user.role.slice(1);
  }, [user]);
  const initials = useMemo(() => {
    if (!user) {
      return "AC";
    }

    return user.full_name
      .split(" ")
      .map((part) => part[0])
      .join("")
      .slice(0, 2)
      .toUpperCase();
  }, [user]);

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <header className="sticky top-0 z-20 border-b border-brand-black/5 bg-brand-light/90 px-4 py-4 backdrop-blur-md sm:px-6 lg:px-8">
      <div className="panel flex flex-col gap-4 px-4 py-4 sm:px-5">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onMenuClick}
              className="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-brand-black/10 bg-white text-brand-black lg:hidden"
              aria-label="Open navigation"
            >
              <MenuIcon className="h-5 w-5" />
            </button>

            <div className="hidden h-11 w-11 items-center justify-center rounded-2xl bg-brand-light lg:flex">
              <img src={logoUrl} alt="AegisCore mark" className="h-8 w-8 object-contain" />
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.26em] text-brand-orange">
                AegisCore SOC
              </p>
              <h1 className="text-xl font-semibold text-brand-black sm:text-2xl">{pageTitle}</h1>
              <p className="text-sm text-brand-black/60">{pageDescription}</p>
            </div>
          </div>

          <div className="hidden items-center gap-3 lg:flex">
            <div className="inline-flex items-center rounded-full bg-brand-light px-3 py-1 text-xs font-medium text-brand-black/70">
              Authenticated workspace
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <label className="input-shell flex min-w-0 flex-1 items-center gap-3">
            <SearchIcon className="h-4 w-4 text-brand-black/45" />
            <input
              type="text"
              placeholder="Search alerts, incidents, assets, or analysts"
              className="w-full bg-transparent text-sm text-brand-black outline-none placeholder:text-brand-black/40"
            />
          </label>

          <div className="flex items-center gap-3">
            <button
              type="button"
              className="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-brand-black/10 bg-white text-brand-black"
              aria-label="Notifications"
            >
              <BellIcon className="h-5 w-5" />
            </button>

            <button
              type="button"
              className="inline-flex items-center gap-3 rounded-2xl border border-brand-black/10 bg-white px-3 py-2.5 text-left"
            >
              <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-brand-orange text-sm font-semibold text-white">
                {initials}
              </div>
              <div className="hidden sm:block">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-semibold text-brand-black">
                    {user?.full_name ?? "AegisCore User"}
                  </p>
                  <span className="rounded-full bg-brand-orange/10 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-[0.14em] text-brand-orange">
                    {roleLabel}
                  </span>
                </div>
                <p className="text-xs text-brand-black/55">{user?.email ?? "No active session"}</p>
              </div>
              <ChevronDownIcon className="h-4 w-4 text-brand-black/45" />
            </button>

            <button type="button" onClick={handleLogout} className="btn-secondary">
              Logout
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
