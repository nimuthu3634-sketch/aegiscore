import { cn } from "@/lib/utils";

export function FormField({
  label,
  hint,
  error,
  className,
  children,
}: {
  label: string;
  hint?: string;
  error?: string;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <label className={cn("grid gap-2", className)}>
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm font-medium text-[#111111]">{label}</span>
        {hint ? <span className="text-xs text-[#8a8a8a]">{hint}</span> : null}
      </div>
      {children}
      {error ? <span className="text-sm text-red-600">{error}</span> : null}
    </label>
  );
}
