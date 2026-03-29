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
    <Card className="overflow-hidden">
      <CardContent className="space-y-3">
        <div className="flex items-start justify-between gap-4">
          <p className="text-sm text-[#6f6f6f]">{label}</p>
          {tone ? <Badge tone={tone}>{tone}</Badge> : null}
        </div>
        <p className="text-3xl font-semibold tracking-[-0.03em] text-[#111111]">{value}</p>
        {detail ? <p className="text-sm text-[#6f6f6f]">{detail}</p> : null}
      </CardContent>
    </Card>
  );
}
