import type { ReactNode } from "react";

type StatCardProps = {
  label: string;
  value: string;
  change: string;
  helper?: string;
  icon?: ReactNode;
  tone?: "orange" | "dark" | "critical" | "success";
};

const toneClasses: Record<
  NonNullable<StatCardProps["tone"]>,
  { card: string; icon: string; accent: string }
> = {
  orange: {
    card: "from-brand-orange/14 via-brand-orange/5 to-white",
    icon: "bg-brand-orange text-brand-white shadow-float",
    accent: "bg-brand-orange/10 text-brand-orange ring-brand-orange/15",
  },
  dark: {
    card: "from-brand-black/8 via-brand-black/[0.03] to-white",
    icon: "bg-brand-surface text-brand-white shadow-panel",
    accent: "bg-brand-black/5 text-brand-black/72 ring-brand-black/10",
  },
  critical: {
    card: "from-red-100 via-red-50 to-white",
    icon: "bg-red-600 text-white shadow-panel",
    accent: "bg-red-100 text-red-700 ring-red-200",
  },
  success: {
    card: "from-emerald-100 via-emerald-50 to-white",
    icon: "bg-emerald-600 text-white shadow-panel",
    accent: "bg-emerald-100 text-emerald-700 ring-emerald-200",
  },
};

export function StatCard({
  label,
  value,
  change,
  helper,
  icon,
  tone = "orange",
}: StatCardProps) {
  const styles = toneClasses[tone];

  return (
    <div className={`panel relative overflow-hidden rounded-[1.9rem] bg-gradient-to-br p-5 sm:p-6 ${styles.card}`}>
      <div className="absolute inset-x-5 top-0 h-px bg-gradient-to-r from-transparent via-brand-orange/20 to-transparent" />

      <div className="relative flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-brand-black/62">{label}</p>
          <p className="mt-4 text-3xl font-semibold tracking-tight text-brand-black sm:text-[2rem]">
            {value}
          </p>
        </div>
        {icon ? (
          <div className={`flex h-12 w-12 items-center justify-center rounded-[1.15rem] ${styles.icon}`}>
            {icon}
          </div>
        ) : null}
      </div>

      <div className="relative mt-6 flex flex-wrap items-center gap-3">
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ring-1 ring-inset ${styles.accent}`}>
          {change}
        </span>
        {helper ? <p className="text-xs leading-5 text-brand-black/55">{helper}</p> : null}
      </div>
    </div>
  );
}
