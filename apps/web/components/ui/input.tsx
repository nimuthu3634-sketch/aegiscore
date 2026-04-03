import { cn } from "@/lib/utils";

export function Input({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-12 w-full rounded-[18px] border border-black/10 bg-white/90 px-4 py-2 text-sm text-[var(--foreground)] outline-none shadow-[inset_0_1px_0_rgba(255,255,255,0.65)] transition placeholder:text-[#958a80] focus:border-[#ff9d57] focus:ring-4 focus:ring-[rgba(255,122,26,0.12)]",
        className,
      )}
      {...props}
    />
  );
}
