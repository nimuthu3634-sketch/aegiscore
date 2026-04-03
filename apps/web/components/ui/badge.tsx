import { cn } from "@/lib/utils";

const tones: Record<string, string> = {
  critical: "border border-[#2d2118] bg-[#171311] text-[#ffd7bb]",
  high: "border border-[#ffd2b2] bg-[#fff1e5] text-[#b4520b]",
  medium: "border border-[#ead6bf] bg-[#fbf3e8] text-[#7d5a33]",
  low: "border border-[#d2ead5] bg-[#eff8f0] text-[#2f6b40]",
  resolved: "border border-[#d2ead5] bg-[#eff8f0] text-[#2f6b40]",
  open: "border border-[#2d2118] bg-[#171311] text-[#ffd7bb]",
  investigating: "border border-[#ffd2b2] bg-[#fff1e5] text-[#b4520b]",
  triaged: "border border-[#ead6bf] bg-[#fbf3e8] text-[#7d5a33]",
  contained: "border border-[#ffd2b2] bg-[#fff1e5] text-[#b4520b]",
  monitoring: "border border-[#ead6bf] bg-[#fbf3e8] text-[#7d5a33]",
  healthy: "border border-[#d2ead5] bg-[#eff8f0] text-[#2f6b40]",
  degraded: "border border-[#ead6bf] bg-[#fbf3e8] text-[#7d5a33]",
  offline: "border border-[#f1c9c9] bg-[#fff1f1] text-[#ab3030]",
  connected: "border border-[#d2ead5] bg-[#eff8f0] text-[#2f6b40]",
  connecting: "border border-[#ead6bf] bg-[#fbf3e8] text-[#7d5a33]",
  disconnected: "border border-[#d8d2cb] bg-[#f4f1ee] text-[#665d55]",
  error: "border border-[#f1c9c9] bg-[#fff1f1] text-[#ab3030]",
};

export function Badge({ tone, className, children }: { tone: string; className?: string; children: React.ReactNode }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[0.72rem] font-semibold capitalize tracking-[0.08em]",
        tones[tone] ?? "border border-gray-200 bg-gray-50 text-gray-700",
        className,
      )}
    >
      {children}
    </span>
  );
}
