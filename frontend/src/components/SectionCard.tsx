import type { ReactNode } from "react";

type SectionCardProps = {
  title: string;
  description?: string;
  eyebrow?: string;
  action?: ReactNode;
  children: ReactNode;
  tone?: "light" | "dark";
  className?: string;
};

export function SectionCard({
  title,
  description,
  eyebrow,
  action,
  children,
  tone = "light",
  className = "",
}: SectionCardProps) {
  const baseClasses =
    tone === "dark"
      ? "rounded-[1.75rem] border border-brand-white/10 bg-brand-surface p-6 text-white shadow-panel"
      : "panel rounded-[1.75rem] p-6";
  const combinedClasses = `${baseClasses} ${className}`.trim();

  return (
    <section className={combinedClasses}>
      <div className="mb-5 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          {eyebrow ? (
            <p
              className={
                tone === "dark"
                  ? "text-xs font-semibold uppercase tracking-[0.24em] text-brand-muted"
                  : "text-xs font-semibold uppercase tracking-[0.24em] text-brand-orange"
              }
            >
              {eyebrow}
            </p>
          ) : null}
          <h2 className="mt-2 text-xl font-semibold">{title}</h2>
          {description ? (
            <p
              className={
                tone === "dark" ? "mt-2 text-sm text-brand-muted" : "mt-2 text-sm text-brand-black/60"
              }
            >
              {description}
            </p>
          ) : null}
        </div>
        {action ? <div className="shrink-0">{action}</div> : null}
      </div>
      {children}
    </section>
  );
}
