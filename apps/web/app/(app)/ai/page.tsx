"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { formatDate, toTitleCase } from "@/lib/format";
import type { ModelMetadata } from "@/types/domain";

type RetrainResponse = {
  job_id: string;
  status: string;
};

type JobRecord = {
  id: string;
  status: string;
  result: Record<string, string | number>;
  error_message?: string | null;
};

export default function AiPage() {
  const queryClient = useQueryClient();
  const [jobId, setJobId] = useState<string | null>(null);
  const { data: model, isLoading } = useQuery({
    queryKey: ["model"],
    queryFn: () => api.get<ModelMetadata>("/ml/model"),
  });
  const retrain = useMutation({
    mutationFn: () => api.post<RetrainResponse>("/ml/retrain"),
    onSuccess: (job) => setJobId(job.job_id),
  });
  const { data: job } = useQuery({
    queryKey: ["model-job", jobId],
    queryFn: () => api.get<JobRecord>(`/jobs/${jobId}`),
    enabled: Boolean(jobId),
    refetchInterval: 5000,
  });

  return (
    <AppShell title="Explainable AI">
      {isLoading || !model ? (
        <div className="rounded-2xl border bg-white p-8 shadow-panel">Loading model metadata...</div>
      ) : (
        <div className="grid gap-6 xl:grid-cols-[1fr_0.9fr]">
          <Card>
            <CardHeader>
              <div>
                <CardTitle>{model.model_name}</CardTitle>
                <p className="mt-2 text-sm text-[var(--muted)]">{model.notes}</p>
              </div>
              <Badge tone="healthy">{model.version}</Badge>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-2xl border px-4 py-3">
                  <p className="text-xs uppercase tracking-wide text-[var(--muted)]">Trained at</p>
                  <p className="mt-2 font-semibold">{formatDate(model.trained_at)}</p>
                </div>
                <div className="rounded-2xl border px-4 py-3">
                  <p className="text-xs uppercase tracking-wide text-[var(--muted)]">Accuracy</p>
                  <p className="mt-2 font-semibold">{model.metrics.accuracy ?? "N/A"}</p>
                </div>
              </div>
              <div className="rounded-2xl border px-4 py-4">
                <p className="font-semibold">Feature inputs</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {model.feature_names.map((feature) => (
                    <Badge key={feature} tone="medium">
                      {toTitleCase(feature)}
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Model operations</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button onClick={() => retrain.mutate()} disabled={retrain.isPending}>
                {retrain.isPending ? "Queueing retrain..." : "Queue retrain job"}
              </Button>
              {job ? (
                <div className="rounded-2xl border px-4 py-3">
                  <div className="flex items-center justify-between gap-3">
                    <p className="font-semibold">Job {job.id}</p>
                    <Badge tone={job.status === "succeeded" ? "healthy" : job.status === "failed" ? "critical" : "medium"}>
                      {job.status}
                    </Badge>
                  </div>
                  <pre className="mt-3 overflow-x-auto rounded-xl bg-[#111111] p-3 text-xs text-white">
                    {JSON.stringify(job.result ?? { error: job.error_message }, null, 2)}
                  </pre>
                </div>
              ) : null}
            </CardContent>
          </Card>
        </div>
      )}
    </AppShell>
  );
}
