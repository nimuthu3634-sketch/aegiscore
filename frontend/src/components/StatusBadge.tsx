type StatusBadgeProps = {
  variant:
    | "new"
    | "triaged"
    | "open"
    | "in_progress"
    | "investigating"
    | "resolved"
    | "assigned"
    | "unassigned"
    | "escalated"
    | "draft"
    | "scheduled"
    | "ready"
    | "connected"
    | "degraded"
    | "offline"
    | "pending"
    | "running"
    | "stopped"
    | "paused"
    | "provisioning";
  children: string;
};

const variantClasses: Record<StatusBadgeProps["variant"], string> = {
  new: "bg-brand-orange/10 text-brand-orange ring-brand-orange/20",
  triaged: "bg-sky-100 text-sky-700 ring-sky-200",
  open: "bg-brand-black/5 text-brand-black/70 ring-brand-black/10",
  in_progress: "bg-violet-100 text-violet-700 ring-violet-200",
  investigating: "bg-violet-100 text-violet-700 ring-violet-200",
  resolved: "bg-emerald-100 text-emerald-700 ring-emerald-200",
  assigned: "bg-emerald-100 text-emerald-700 ring-emerald-200",
  unassigned: "bg-brand-black/5 text-brand-black/70 ring-brand-black/10",
  escalated: "bg-red-100 text-red-700 ring-red-200",
  draft: "bg-brand-black/5 text-brand-black/70 ring-brand-black/10",
  scheduled: "bg-sky-100 text-sky-700 ring-sky-200",
  ready: "bg-emerald-100 text-emerald-700 ring-emerald-200",
  connected: "bg-emerald-100 text-emerald-700 ring-emerald-200",
  degraded: "bg-amber-100 text-amber-700 ring-amber-200",
  offline: "bg-red-100 text-red-700 ring-red-200",
  pending: "bg-brand-black/5 text-brand-black/70 ring-brand-black/10",
  running: "bg-emerald-100 text-emerald-700 ring-emerald-200",
  stopped: "bg-brand-black/5 text-brand-black/70 ring-brand-black/10",
  paused: "bg-amber-100 text-amber-700 ring-amber-200",
  provisioning: "bg-sky-100 text-sky-700 ring-sky-200",
};

export function StatusBadge({ variant, children }: StatusBadgeProps) {
  return (
    <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold capitalize ring-1 ${variantClasses[variant]}`}>
      {children}
    </span>
  );
}
