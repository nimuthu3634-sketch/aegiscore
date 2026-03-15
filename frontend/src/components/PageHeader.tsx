import type { ReactNode } from "react";

type PageHeaderProps = {
  eyebrow?: string;
  title: string;
  description: string;
  action?: ReactNode;
};

export function PageHeader({ eyebrow, title, description, action }: PageHeaderProps) {
  return (
    <div className="mb-6 rounded-[1.75rem] border border-brand-black/5 bg-white p-6 shadow-panel">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          {eyebrow ? (
            <p className="text-xs uppercase tracking-[0.24em] text-brand-orange">{eyebrow}</p>
          ) : null}
          <h2 className="mt-2 text-2xl font-semibold text-brand-black">{title}</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-brand-black/70">{description}</p>
        </div>
        {action ? <div className="shrink-0">{action}</div> : null}
      </div>
    </div>
  );
}
