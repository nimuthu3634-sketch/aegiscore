import type { ReactNode } from "react";

type StatCardProps = {
  label: string;
  value: string;
  change: string;
  helper?: string;
  icon?: ReactNode;
  tone?: "orange" | "dark" | "critical" | "success";
};

const toneClasses: Record<NonNullable<StatCardProps["tone"]>, string> = {
  orange: "from-brand-orange/12 to-white",
  dark: "from-brand-black/8 to-white",
  critical: "from-red-100 to-white",
  success: "from-emerald-100 to-white",
};

export function StatCard({
  label,
  value,
  change,
  helper,
  icon,
  tone = "orange",
}: StatCardProps) {
  return (
    <div
      className={`panel rounded-[1.75rem] bg-gradient-to-br p-5 ${toneClasses[tone]}`}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-brand-black/60">{label}</p>
          <p className="mt-4 text-3xl font-semibold tracking-tight text-brand-black">{value}</p>
        </div>
        {icon ? (
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-brand-orange shadow-sm">
            {icon}
          </div>
        ) : null}
      </div>

      <div className="mt-5 flex items-center justify-between gap-3">
        <span className="rounded-full bg-white/90 px-3 py-1 text-xs font-semibold text-brand-black">
          {change}
        </span>
        {helper ? <p className="text-xs text-brand-black/55">{helper}</p> : null}
      </div>
    </div>
  );
}
