import { TriangleAlert } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export function ErrorState({
  title = "Something went wrong",
  description,
  onRetry,
}: {
  title?: string;
  description: string;
  onRetry?: () => void;
}) {
  return (
    <Card className="border-red-100 bg-red-50/40">
      <CardContent className="flex flex-col items-start gap-4 py-8">
        <div className="rounded-full bg-white p-3 text-red-600">
          <TriangleAlert className="h-5 w-5" />
        </div>
        <div className="space-y-2">
          <h3 className="text-lg font-semibold text-[#111111]">{title}</h3>
          <p className="text-sm text-[#6f6f6f]">{description}</p>
        </div>
        {onRetry ? (
          <Button variant="outline" onClick={onRetry}>
            Try again
          </Button>
        ) : null}
      </CardContent>
    </Card>
  );
}
