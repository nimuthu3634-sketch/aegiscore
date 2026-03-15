import type { SeverityLevel } from "@/types/domain";

type SeverityBadgeProps = {
  level: SeverityLevel;
};

const severityStyles: Record<SeverityLevel, string> = {
  critical: "bg-red-100 text-red-700 ring-red-200",
  high: "bg-orange-100 text-orange-700 ring-orange-200",
  medium: "bg-amber-100 text-amber-700 ring-amber-200",
  low: "bg-emerald-100 text-emerald-700 ring-emerald-200",
};

export function SeverityBadge({ level }: SeverityBadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold capitalize ring-1 ${severityStyles[level]}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {level}
    </span>
  );
}
