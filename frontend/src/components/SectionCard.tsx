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
      ? "relative overflow-hidden rounded-[1.9rem] border border-brand-white/10 bg-brand-surface p-6 text-white shadow-premium sm:p-7"
      : "panel relative overflow-hidden rounded-[1.9rem] p-6 shadow-soft sm:p-7";
  const combinedClasses = `${baseClasses} ${className}`.trim();

  return (
    <section className={combinedClasses}>
      <div
        className={
          tone === "dark"
            ? "pointer-events-none absolute -right-10 top-0 h-36 w-36 rounded-full bg-brand-orange/12 blur-3xl"
            : "pointer-events-none absolute -right-12 top-0 h-32 w-32 rounded-full bg-brand-orange/10 blur-3xl"
        }
      />
      <div
        className={
          tone === "dark"
            ? "absolute inset-x-6 top-0 h-px bg-gradient-to-r from-transparent via-brand-orange/60 to-transparent"
            : "absolute inset-x-6 top-0 h-px bg-gradient-to-r from-transparent via-brand-orange/30 to-transparent"
        }
      />

      <div className="relative mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="max-w-3xl">
          {eyebrow ? (
            <p
              className={
                tone === "dark"
                  ? "text-xs font-semibold uppercase tracking-[0.26em] text-brand-muted"
                  : "text-xs font-semibold uppercase tracking-[0.26em] text-brand-orange"
              }
            >
              {eyebrow}
            </p>
          ) : null}
          <h2 className="mt-2 text-xl font-semibold tracking-tight sm:text-[1.35rem]">{title}</h2>
          {description ? (
            <p
              className={
                tone === "dark"
                  ? "mt-3 text-sm leading-7 text-brand-muted"
                  : "mt-3 text-sm leading-7 text-brand-black/62"
              }
            >
              {description}
            </p>
          ) : null}
        </div>
        {action ? <div className="relative shrink-0">{action}</div> : null}
      </div>
      <div className="relative">{children}</div>
    </section>
  );
}
