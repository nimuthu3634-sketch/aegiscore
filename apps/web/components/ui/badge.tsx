import { cn } from "@/lib/utils";

const tones: Record<string, string> = {
  critical: "bg-red-100 text-red-700",
  high: "bg-orange-100 text-orange-700",
  medium: "bg-amber-100 text-amber-700",
  low: "bg-emerald-100 text-emerald-700",
  resolved: "bg-emerald-100 text-emerald-700",
  open: "bg-red-100 text-red-700",
  investigating: "bg-orange-100 text-orange-700",
  triaged: "bg-amber-100 text-amber-700",
  healthy: "bg-emerald-100 text-emerald-700",
  degraded: "bg-amber-100 text-amber-700",
  offline: "bg-red-100 text-red-700",
};

export function Badge({ tone, className, children }: { tone: string; className?: string; children: React.ReactNode }) {
  return (
    <span className={cn("inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold", tones[tone] ?? "bg-gray-100 text-gray-700", className)}>
      {children}
    </span>
  );
}
