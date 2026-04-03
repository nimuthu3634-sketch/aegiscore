import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

export function StatCard({
  label,
  value,
  detail,
  tone,
}: {
  label: string;
  value: React.ReactNode;
  detail?: string;
  tone?: string;
}) {
  return (
    <Card className="overflow-hidden bg-[linear-gradient(180deg,rgba(255,255,255,0.94),rgba(251,246,240,0.88))]">
      <CardContent className="space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-2 text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-[#8a7d72]">
            <span className="h-2 w-2 rounded-full bg-[var(--accent)]" />
            <span>{label}</span>
          </div>
          {tone ? <Badge tone={tone}>{tone}</Badge> : null}
        </div>
        <p className="text-4xl font-semibold tracking-[-0.05em] text-[#111111]">{value}</p>
        {detail ? <p className="text-sm leading-6 text-[#6d635a]">{detail}</p> : null}
      </CardContent>
    </Card>
  );
}
