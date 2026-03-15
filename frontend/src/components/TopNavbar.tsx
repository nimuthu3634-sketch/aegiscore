import { useLocation } from "react-router-dom";

import logoUrl from "@repo-assets/aegiscore-logo.svg";

import { navigationItems } from "@/types/navigation";

type TopNavbarProps = {
  onMenuClick: () => void;
};

const pageTitleLookup = new Map(navigationItems.map((item) => [item.path, item.label]));

export function TopNavbar({ onMenuClick }: TopNavbarProps) {
  const location = useLocation();
  const pageTitle = pageTitleLookup.get(location.pathname) ?? "Workspace";

  return (
    <header className="sticky top-0 z-20 border-b border-brand-black/5 bg-brand-light/90 px-4 py-4 backdrop-blur sm:px-6 lg:px-8">
      <div className="rounded-[1.75rem] border border-brand-black/5 bg-white/95 px-4 py-3 shadow-panel sm:px-6">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onMenuClick}
              className="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-brand-black/10 bg-brand-light text-sm font-semibold text-brand-black lg:hidden"
            >
              Menu
            </button>

            <div className="hidden h-11 w-11 items-center justify-center rounded-2xl bg-brand-light lg:flex">
              <img src={logoUrl} alt="AegisCore mark" className="h-8 w-8 object-contain" />
            </div>

            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-brand-orange">
                AegisCore Command
              </p>
              <h1 className="text-xl font-semibold text-brand-black">{pageTitle}</h1>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden rounded-2xl bg-brand-light px-4 py-2 text-sm text-brand-black/70 sm:block">
              Lab-only defensive analytics
            </div>
            <div className="rounded-2xl bg-brand-orange px-4 py-2 text-sm font-semibold text-brand-white">
              Admin Session
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
