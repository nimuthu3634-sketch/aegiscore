import { classNames } from "@/utils/classNames";

type StatusBadgeProps = {
  variant:
    | "critical"
    | "high"
    | "medium"
    | "low"
    | "new"
    | "triaged"
    | "in_progress"
    | "resolved"
    | "connected"
    | "pending";
  children: string;
};

const variantClasses: Record<StatusBadgeProps["variant"], string> = {
  critical: "bg-red-100 text-red-700",
  high: "bg-orange-100 text-orange-700",
  medium: "bg-amber-100 text-amber-700",
  low: "bg-emerald-100 text-emerald-700",
  new: "bg-brand-orange/10 text-brand-orange",
  triaged: "bg-blue-100 text-blue-700",
  in_progress: "bg-violet-100 text-violet-700",
  resolved: "bg-emerald-100 text-emerald-700",
  connected: "bg-emerald-100 text-emerald-700",
  pending: "bg-brand-black/5 text-brand-black/70",
};

export function StatusBadge({ variant, children }: StatusBadgeProps) {
  return (
    <span
      className={classNames(
        "inline-flex rounded-full px-3 py-1 text-xs font-semibold capitalize",
        variantClasses[variant],
      )}
    >
      {children}
    </span>
  );
}
