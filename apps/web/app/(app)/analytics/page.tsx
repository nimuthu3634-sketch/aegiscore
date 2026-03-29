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
import type { Alert, DashboardSummary, JobRecord, PageResult, RiskModelMetadata } from "@/types/domain";

function buildRiskDistribution(alerts: Alert[]) {
  const groups = alerts.reduce<Record<string, number>>((accumulator, alert) => {
    const bucket = alert.risk_score >= 85 ? "Critical" : alert.risk_score >= 65 ? "High" : alert.risk_score >= 35 ? "Medium" : "Low";
    accumulator[bucket] = (accumulator[bucket] ?? 0) + 1;
    return accumulator;
  }, {});
  return Object.entries(groups).map(([name, value]) => ({ name, value }));
}

function buildSourceComparison(alerts: Alert[]) {
  const groups = alerts.reduce<Record<string, { label: string; average: number; count: number; total: number }>>((accumulator, alert) => {
    accumulator[alert.source] = accumulator[alert.source] ?? { label: alert.source, average: 0, count: 0, total: 0 };
    accumulator[alert.source].count += 1;
    accumulator[alert.source].total += alert.risk_score;
    accumulator[alert.source].average = accumulator[alert.source].total / accumulator[alert.source].count;
    return accumulator;
  }, {});
  return Object.values(groups).map((entry) => ({ label: entry.label, average: Number(entry.average.toFixed(1)) }));
}

function buildExplainabilityView(alerts: Alert[]) {
  const groups = alerts.reduce<Record<string, number>>((accumulator, alert) => {
    for (const factor of alert.explainability) {
      accumulator[factor.factor] = (accumulator[factor.factor] ?? 0) + Math.abs(factor.impact);
    }
    return accumulator;
  }, {});
  return Object.entries(groups)
    .sort((left, right) => right[1] - left[1])
    .slice(0, 6)
    .map(([label, total]) => ({ label: toTitleCase(label), total: Number(total.toFixed(2)) }));
}

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
  const alertsQuery = useQuery({
    queryKey: ["alerts", "analytics"],
    queryFn: () => api.get<PageResult<Alert>>(`/alerts${createQueryString({ page: 1, page_size: 100 })}`),
  });

  const retrainMutation = useMutation({
    mutationFn: () => api.post<{ job_id: string; status: string }>("/ml/retrain"),
  });

  const retrainJobQuery = useQuery({
    queryKey: ["jobs", retrainMutation.data?.job_id],
    queryFn: () => api.get<JobRecord>(`/jobs/${retrainMutation.data?.job_id}`),
    enabled: Boolean(retrainMutation.data?.job_id),
    refetchInterval: 5000,
  });

  if (summaryQuery.isLoading || modelQuery.isLoading || alertsQuery.isLoading) {
    return <LoadingState lines={8} />;
  }

  if (summaryQuery.isError || modelQuery.isError || alertsQuery.isError || !summaryQuery.data || !modelQuery.data || !alertsQuery.data) {
    return <ErrorState description="Analytics data could not be loaded from the connected APIs." onRetry={() => { summaryQuery.refetch(); modelQuery.refetch(); alertsQuery.refetch(); }} />;
  }

  const summary = summaryQuery.data;
  const model = modelQuery.data;
  const alerts = alertsQuery.data.items;
  const riskDistribution = buildRiskDistribution(alerts);
  const sourceComparison = buildSourceComparison(alerts);
  const explainability = buildExplainabilityView(alerts);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Analytics and AI"
        title="Explainable risk analytics"
        description="Inspect active model metadata, compare sources, monitor anomaly pressure, and understand the factors that drive alert prioritization."
        actions={
          currentUser?.role === "Admin" ? (
            <Button onClick={() => retrainMutation.mutate()} disabled={retrainMutation.isPending}>
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
              <p className="text-sm text-[#6f6f6f]">Queue a retrain job to watch job state and model output here.</p>
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
