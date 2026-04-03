import { Badge } from "@/components/ui/badge";

export function PageHeader({
  eyebrow,
  title,
  description,
  badge,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description: string;
  badge?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="rounded-[30px] border border-black/8 bg-[linear-gradient(135deg,rgba(255,255,255,0.92),rgba(255,240,228,0.82))] p-6 shadow-[0_20px_52px_rgba(17,17,17,0.07)] backdrop-blur xl:p-8">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-3">
          {eyebrow ? (
            <span className="inline-flex rounded-full border border-[#ffd2b2] bg-[var(--accent-soft)] px-3 py-1 text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-[#a54e10]">
              {eyebrow}
            </span>
          ) : null}
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-3xl font-semibold tracking-[-0.05em] text-[#111111] xl:text-[2.25rem]">{title}</h1>
            {badge ? <Badge tone="medium">{badge}</Badge> : null}
          </div>
          <p className="max-w-3xl text-sm leading-7 text-[#6d635a]">{description}</p>
        </div>
        {actions ? <div className="flex flex-wrap items-center gap-3">{actions}</div> : null}
      </div>
    </div>
  );
}
