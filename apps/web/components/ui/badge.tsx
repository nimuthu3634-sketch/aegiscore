import { cn } from "@/lib/utils";

const tones: Record<string, string> = {
  critical: "border border-red-200 bg-red-50 text-red-700",
  high: "border border-orange-200 bg-orange-50 text-orange-700",
  medium: "border border-amber-200 bg-amber-50 text-amber-700",
  low: "border border-emerald-200 bg-emerald-50 text-emerald-700",
  resolved: "border border-emerald-200 bg-emerald-50 text-emerald-700",
  open: "border border-red-200 bg-red-50 text-red-700",
  investigating: "border border-orange-200 bg-orange-50 text-orange-700",
  triaged: "border border-amber-200 bg-amber-50 text-amber-700",
  contained: "border border-orange-200 bg-orange-50 text-orange-700",
  monitoring: "border border-amber-200 bg-amber-50 text-amber-700",
  healthy: "border border-emerald-200 bg-emerald-50 text-emerald-700",
  degraded: "border border-amber-200 bg-amber-50 text-amber-700",
  offline: "border border-red-200 bg-red-50 text-red-700",
  connected: "border border-emerald-200 bg-emerald-50 text-emerald-700",
  connecting: "border border-amber-200 bg-amber-50 text-amber-700",
  disconnected: "border border-slate-200 bg-slate-50 text-slate-700",
  error: "border border-red-200 bg-red-50 text-red-700",
};

export function Badge({ tone, className, children }: { tone: string; className?: string; children: React.ReactNode }) {
  return (
    <span className={cn("inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold capitalize", tones[tone] ?? "border border-gray-200 bg-gray-50 text-gray-700", className)}>
      {children}
    </span>
  );
}
