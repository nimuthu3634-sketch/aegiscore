"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { useAuth } from "@/hooks/use-auth";
import type { Alert, Incident } from "@/types/domain";

export default function AlertDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: currentUser } = useAuth();
  const { data: alert, isLoading } = useQuery({
    queryKey: ["alert", params.id],
    queryFn: () => api.get<Alert>(`/alerts/${params.id}`),
  });
  const [comment, setComment] = useState("");
  const [incidentTitle, setIncidentTitle] = useState("");

  const updateMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => api.patch<Alert>(`/alerts/${params.id}`, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alert", params.id] }),
  });
  const commentMutation = useMutation({
    mutationFn: () => api.post(`/alerts/${params.id}/comments`, { body: comment }),
    onSuccess: () => {
      setComment("");
      queryClient.invalidateQueries({ queryKey: ["alert", params.id] });
    },
  });
  const incidentMutation = useMutation({
    mutationFn: () =>
      api.post<Incident>(`/alerts/${params.id}/incident`, {
        title: incidentTitle || `Investigation for ${alert?.title}`,
        summary: alert?.description,
        priority: alert?.severity === "critical" ? "P1" : alert?.severity === "high" ? "P2" : "P3",
        linked_alert_ids: [params.id],
        evidence: [],
      }),
    onSuccess: (incident) => router.push(`/incidents/${incident.id}`),
  });

  return (
    <AppShell title="Alert Detail">
      {isLoading || !alert ? (
        <div className="rounded-2xl border bg-white p-8 shadow-panel">Loading alert...</div>
      ) : (
        <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>{alert.title}</CardTitle>
                  <p className="mt-2 text-sm text-[var(--muted)]">{alert.description}</p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone={alert.severity}>{alert.severity}</Badge>
                  <Badge tone={alert.status}>{alert.status}</Badge>
                  <Badge tone={alert.risk_label ?? "low"}>{alert.risk_score}</Badge>
                </div>
              </CardHeader>
              <CardContent className="grid gap-4 md:grid-cols-2">
                <div>
                  <p className="text-xs uppercase tracking-wide text-[var(--muted)]">Source</p>
                  <p className="mt-2 font-semibold">{alert.source}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide text-[var(--muted)]">Asset</p>
                  <p className="mt-2 font-semibold">{alert.asset?.hostname ?? "Unmapped"}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide text-[var(--muted)]">Detected</p>
                  <p className="mt-2 font-semibold">{formatDate(alert.detected_at)}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide text-[var(--muted)]">Assignee</p>
                  <p className="mt-2 font-semibold">{alert.assignee?.full_name ?? "Unassigned"}</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Explainable risk factors</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {alert.explainability.map((factor) => (
                  <div key={factor.factor} className="rounded-2xl border px-4 py-3">
                    <p className="font-semibold">{factor.factor}</p>
                    <p className="mt-1 text-sm text-[var(--muted)]">Impact score: {factor.impact}</p>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Comments</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Textarea placeholder="Add triage context or decision notes" value={comment} onChange={(event) => setComment(event.target.value)} />
                <Button onClick={() => commentMutation.mutate()} disabled={!comment || commentMutation.isPending}>
                  Add comment
                </Button>
                <div className="space-y-3">
                  {alert.comments.map((entry) => (
                    <div key={entry.id} className="rounded-2xl border px-4 py-3">
                      <div className="flex items-center justify-between gap-3">
                        <p className="font-semibold">{entry.author?.full_name ?? "System"}</p>
                        <p className="text-xs uppercase tracking-wide text-[var(--muted)]">{formatDate(entry.created_at)}</p>
                      </div>
                      <p className="mt-2 text-sm">{entry.body}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Triage actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Select value={alert.status} onChange={(event) => updateMutation.mutate({ status: event.target.value })}>
                  <option value="open">Open</option>
                  <option value="triaged">Triaged</option>
                  <option value="investigating">Investigating</option>
                  <option value="resolved">Resolved</option>
                  <option value="suppressed">Suppressed</option>
                </Select>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => updateMutation.mutate({ assigned_to_id: currentUser?.id })}
                  disabled={!currentUser}
                >
                  Assign to me
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Create incident</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Input
                  value={incidentTitle}
                  onChange={(event) => setIncidentTitle(event.target.value)}
                  placeholder={`Investigation for ${alert.title}`}
                />
                <Button className="w-full" onClick={() => incidentMutation.mutate()} disabled={incidentMutation.isPending}>
                  Open incident
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Response recommendations</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {alert.recommendations.map((recommendation) => (
                  <div key={recommendation} className="rounded-2xl border px-4 py-3 text-sm">
                    {recommendation}
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </AppShell>
  );
}
