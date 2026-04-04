"use client";

import { useMutation, useQuery } from "@tanstack/react-query";

import { AlertTrendChart } from "@/components/charts/alert-trend-chart";
import { ComparisonBarChart } from "@/components/charts/comparison-bar-chart";
import { DonutChart } from "@/components/charts/donut-chart";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { PageHeader } from "@/components/shared/page-header";
import { StatCard } from "@/components/shared/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, createQueryString } from "@/lib/api";
import { formatDate, formatPercent, scoreTone, toTitleCase } from "@/lib/format";
import { useAuth } from "@/hooks/use-auth";
import type { DashboardSummary, HealthResponse, JobRecord, PageResult, RiskModelMetadata, RiskOverview } from "@/types/domain";

export default function AnalyticsPage() {
  const { data: currentUser } = useAuth();
  const summaryQuery = useQuery({
    queryKey: ["dashboard", "summary", "analytics"],
    queryFn: () => api.get<DashboardSummary>("/dashboard/summary"),
  });
  const modelQuery = useQuery({
    queryKey: ["ml", "model"],
    queryFn: () => api.get<RiskModelMetadata>("/ml/model"),
  });
  const modelsQuery = useQuery({
    queryKey: ["ml", "models"],
    queryFn: () => api.get<PageResult<RiskModelMetadata>>(`/ml/models${createQueryString({ page: 1, page_size: 8 })}`),
  });
  const overviewQuery = useQuery({
    queryKey: ["ml", "overview"],
    queryFn: () => api.get<RiskOverview>("/ml/overview"),
  });
  const healthQuery = useQuery({
    queryKey: ["health", "analytics"],
    queryFn: () => api.get<HealthResponse>("/health"),
    retry: false,
  });

  const retrainMutation = useMutation({
    mutationFn: () => api.post<{ job_id: string; status: string }>("/ml/retrain"),
  });

  const retrainJobQuery = useQuery({
    queryKey: ["jobs", retrainMutation.data?.job_id],
    queryFn: () => api.get<JobRecord>(`/admin/jobs/${retrainMutation.data?.job_id}`),
    enabled: Boolean(retrainMutation.data?.job_id),
    refetchInterval: (query) => (query.state.data?.status === "running" || query.state.data?.status === "queued" ? 3000 : false),
  });

  const noModelYet = modelQuery.isError && (modelQuery.error as { status?: number } | null)?.status === 404;
  const queueUnavailableDetail =
    healthQuery.data && healthQuery.data.redis.status !== "ok"
      ? healthQuery.data.redis.detail ?? "Redis-backed background processing is unavailable."
      : null;
  const retrainBlockedReason = queueUnavailableDetail
    ? `${queueUnavailableDetail} Start Redis and the worker before queueing retraining.`
    : undefined;

  if (summaryQuery.isLoading || modelQuery.isLoading || overviewQuery.isLoading) {
    return <LoadingState lines={8} />;
  }

  if (summaryQuery.isError || overviewQuery.isError || !summaryQuery.data || !overviewQuery.data) {
    return <ErrorState description="Analytics data could not be loaded from the connected APIs." onRetry={() => { summaryQuery.refetch(); modelQuery.refetch(); overviewQuery.refetch(); }} />;
  }

  if (noModelYet) {
    return (
      <div className="space-y-6">
        <PageHeader
          eyebrow="Analytics and AI"
          title="Explainable risk analytics"
          description="No trained model found. Import telemetry data and queue a retrain job to activate AI risk scoring."
          actions={
            currentUser?.role === "Admin" ? (
              <Button onClick={() => retrainMutation.mutate()} disabled={retrainMutation.isPending || Boolean(queueUnavailableDetail)} title={retrainBlockedReason}>
                {retrainMutation.isPending ? "Queueing retrain..." : "Queue retrain job"}
              </Button>
            ) : null
          }
        />
        <Card>
          <CardContent className="space-y-4 py-12 text-center text-sm text-[#6f6f6f]">
            <p>No risk model has been trained yet. An Admin can queue the first training run above.</p>
            {queueUnavailableDetail ? (
              <div className="rounded-[1.25rem] border border-amber-200 bg-amber-50 px-4 py-3 text-left text-sm text-amber-800">
                Background training is currently unavailable. {retrainBlockedReason}
              </div>
            ) : null}
            {retrainMutation.error instanceof Error ? (
              <div className="rounded-[1.25rem] border border-red-200 bg-red-50 px-4 py-3 text-left text-sm text-red-700">
                {retrainMutation.error.message}
              </div>
            ) : null}
            {retrainJobQuery.data ? (
              <div className="mt-4">
                <Badge tone={retrainJobQuery.data.status === "succeeded" ? "healthy" : retrainJobQuery.data.status === "failed" ? "critical" : "medium"}>
                  Job {retrainJobQuery.data.status}
                </Badge>
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (modelQuery.isError) {
    return <ErrorState description="Risk model metadata could not be loaded." onRetry={() => modelQuery.refetch()} />;
  }

  const summary = summaryQuery.data;
  const model = modelQuery.data!;
  const overview = overviewQuery.data;
  const riskDistribution = overview.risk_distribution.map((item) => ({ name: item.band, value: item.count }));
  const sourceComparison = overview.source_comparison.map((item) => ({ label: item.source, average: item.average_risk_score }));
  const explainability = overview.top_explanations.map((item) => ({ label: toTitleCase(item.factor), total: item.total_impact }));

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Analytics and AI"
        title="Explainable risk analytics"
        description="Inspect active model metadata, compare sources, monitor anomaly pressure, and understand the factors that drive alert prioritization."
        actions={
          currentUser?.role === "Admin" ? (
            <Button onClick={() => retrainMutation.mutate()} disabled={retrainMutation.isPending || Boolean(queueUnavailableDetail)} title={retrainBlockedReason}>
              {retrainMutation.isPending ? "Queueing retrain..." : "Queue retrain job"}
            </Button>
          ) : null
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Active model" value={model.version} detail={model.model_name} tone="healthy" />
        <StatCard label="Accuracy" value={formatPercent(model.metrics.accuracy)} detail="Most recent validation accuracy" />
        <StatCard label="Training samples" value={String(model.metrics.samples ?? "N/A")} detail="Samples used in last training run" />
        <StatCard label="Open alert mean" value={summary.kpis.average_risk_score.toFixed(1)} detail="Average risk score across active alerts" tone={scoreTone(summary.kpis.average_risk_score)} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <Card>
          <CardHeader>
            <CardTitle>Model summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-[1.25rem] border bg-[#fcfcfc] p-4 text-sm leading-6 text-[#5f5f5f]">{model.notes}</div>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-[1.25rem] border bg-[#fcfcfc] p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Trained at</p>
                <p className="mt-3 font-semibold">{formatDate(model.trained_at)}</p>
              </div>
              <div className="rounded-[1.25rem] border bg-[#fcfcfc] p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Active</p>
                <div className="mt-3">
                  <Badge tone={model.is_active ? "healthy" : "offline"}>{model.is_active ? "Active" : "Inactive"}</Badge>
                </div>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              {model.feature_names.map((feature) => (
                <Badge key={feature} tone="medium">
                  {toTitleCase(feature)}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Queued training job</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {queueUnavailableDetail ? (
              <div className="rounded-[1.25rem] border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-800">
                Retraining depends on Redis-backed background processing. {retrainBlockedReason}
              </div>
            ) : null}
            {retrainMutation.error instanceof Error ? (
              <div className="rounded-[1.25rem] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {retrainMutation.error.message}
              </div>
            ) : null}
            {retrainJobQuery.data ? (
              <>
                <div className="flex items-center justify-between gap-3 rounded-[1.25rem] border bg-[#fcfcfc] p-4">
                  <div>
                    <p className="font-semibold text-[#111111]">{retrainJobQuery.data.job_type}</p>
                    <p className="mt-1 text-sm text-[#6f6f6f]">Queued {formatDate(retrainJobQuery.data.queued_at)}</p>
                  </div>
                  <Badge tone={retrainJobQuery.data.status === "succeeded" ? "healthy" : retrainJobQuery.data.status === "failed" ? "critical" : "medium"}>
                    {retrainJobQuery.data.status}
                  </Badge>
                </div>
                <pre className="overflow-x-auto rounded-[1.5rem] border bg-[#111111] p-5 text-xs leading-6 text-white">
                  {JSON.stringify(retrainJobQuery.data.result ?? { error: retrainJobQuery.data.error_message }, null, 2)}
                </pre>
              </>
            ) : (
              <p className="text-sm text-[#6f6f6f]">Queue a retrain job to watch the background job state and model output here.</p>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Risk distribution</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 lg:grid-cols-[220px_1fr]">
            <DonutChart data={riskDistribution.length ? riskDistribution : [{ name: "Low", value: 0 }]} />
            <div className="space-y-3">
              {riskDistribution.map((item) => (
                <div key={item.name} className="flex items-center justify-between rounded-2xl border px-4 py-3">
                  <span className="font-medium">{item.name}</span>
                  <Badge tone={item.name.toLowerCase()}>{item.value}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Source comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <ComparisonBarChart data={sourceComparison.length ? sourceComparison : [{ label: "No data", average: 0 }]} dataKey="average" />
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <CardHeader>
            <CardTitle>Anomaly trend</CardTitle>
          </CardHeader>
          <CardContent>
            <AlertTrendChart data={summary.alert_trend} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top explainability factors</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {explainability.map((item) => (
              <div key={item.label} className="flex items-center justify-between rounded-[1.25rem] border bg-[#fcfcfc] px-4 py-3">
                <span className="font-medium">{item.label}</span>
                <Badge tone="medium">{item.total.toFixed(2)}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent model versions</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {(modelsQuery.data?.items ?? []).map((entry) => (
            <div key={entry.id} className="rounded-[1.25rem] border bg-[#fcfcfc] p-4">
              <div className="flex items-center justify-between gap-3">
                <p className="font-semibold text-[#111111]">{entry.version}</p>
                <Badge tone={entry.is_active ? "healthy" : "disconnected"}>{entry.is_active ? "Active" : "Historical"}</Badge>
              </div>
              <p className="mt-2 text-sm text-[#6f6f6f]">{formatDate(entry.trained_at)}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
