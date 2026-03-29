import type { ReactNode } from "react";

import { brandName, brandPalette } from "@aegiscore/config";

function ShieldIcon() {
  return (
    <svg
      aria-hidden="true"
      className="h-4 w-4"
      fill="none"
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M12 3.5 5.5 6v5.4c0 4.4 2.6 8.5 6.5 10.1 3.9-1.6 6.5-5.7 6.5-10.1V6L12 3.5Z"
        stroke={brandPalette.primaryOrange}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
      <path
        d="m9.6 12.2 1.7 1.7 3.1-3.5"
        stroke={brandPalette.primaryOrange}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

export function BrandHero({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children?: ReactNode;
}) {
  return (
    <div className="rounded-[2rem] bg-[#111111] p-8 text-white shadow-panel">
      <div className="inline-flex items-center gap-3 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white/80">
        <ShieldIcon />
        {brandName} defensive SOC
      </div>
      <h1 className="mt-8 max-w-xl text-4xl font-semibold leading-tight">{title}</h1>
      <p className="mt-4 max-w-xl text-base text-white/70">{description}</p>
      {children ? <div className="mt-10 grid gap-4 sm:grid-cols-3">{children}</div> : null}
    </div>
  );
}
