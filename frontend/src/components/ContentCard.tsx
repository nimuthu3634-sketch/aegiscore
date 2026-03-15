import type { ReactNode } from "react";

type ContentCardProps = {
  title: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
};

export function ContentCard({ title, description, action, children }: ContentCardProps) {
  return (
    <section className="rounded-[1.5rem] border border-brand-black/5 bg-white p-5 shadow-panel">
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="text-lg font-semibold text-brand-black">{title}</h3>
          {description ? (
            <p className="mt-1 text-sm leading-6 text-brand-black/60">{description}</p>
          ) : null}
        </div>
        {action ? <div className="shrink-0">{action}</div> : null}
      </div>
      {children}
    </section>
  );
}
