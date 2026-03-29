import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function LoadingState({
  lines = 4,
  compact = false,
}: {
  lines?: number;
  compact?: boolean;
}) {
  return (
    <Card>
      <CardContent className="space-y-3 py-6">
        <Skeleton className="h-6 w-48" />
        {Array.from({ length: lines }).map((_, index) => (
          <Skeleton key={index} className={compact ? "h-10 w-full" : "h-16 w-full"} />
        ))}
      </CardContent>
    </Card>
  );
}
