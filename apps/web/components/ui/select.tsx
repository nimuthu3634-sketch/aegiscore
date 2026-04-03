import { cn } from "@/lib/utils";

export function Select({ className, children, ...props }: React.SelectHTMLAttributes<HTMLSelectElement>) {
  const accessibleTitle =
    props.title ??
    (typeof props["aria-label"] === "string" ? props["aria-label"] : undefined) ??
    (typeof props.name === "string" && props.name.length > 0
      ? props.name
          .replace(/[_-]+/g, " ")
          .replace(/\b\w/g, (character) => character.toUpperCase())
      : undefined);

  return (
    <select
      className={cn(
        "h-11 w-full rounded-xl border bg-white px-3 py-2 text-sm outline-none transition focus:border-[var(--accent)] focus:ring-2 focus:ring-[rgba(255,122,26,0.15)]",
        className,
      )}
      title={accessibleTitle}
      {...props}
    >
      {children}
    </select>
  );
}
