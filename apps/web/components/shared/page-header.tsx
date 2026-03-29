import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

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
    <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
      <div className="space-y-2">
        {eyebrow ? <p className="text-xs uppercase tracking-[0.28em] text-[#8f8f8f]">{eyebrow}</p> : null}
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-3xl font-semibold tracking-[-0.03em] text-[#111111]">{title}</h1>
          {badge ? <Badge tone="medium">{badge}</Badge> : null}
        </div>
        <p className="max-w-3xl text-sm leading-6 text-[#6f6f6f]">{description}</p>
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-3">{actions}</div> : null}
    </div>
  );
}
