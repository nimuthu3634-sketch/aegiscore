"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { Incident } from "@/types/domain";

export default function IncidentDetailPage() {
  const params = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [note, setNote] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["incident", params.id],
    queryFn: () => api.get<Incident>(`/incidents/${params.id}`),
  });

  const updateMutation = useMutation({
    mutationFn: (payload: Record<string, string>) => api.patch<Incident>(`/incidents/${params.id}`, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["incident", params.id] }),
  });
  const noteMutation = useMutation({
    mutationFn: () => api.post(`/incidents/${params.id}/notes`, { body: note, is_timeline_event: true }),
    onSuccess: () => {
      setNote("");
      queryClient.invalidateQueries({ queryKey: ["incident", params.id] });
    },
  });

  return (
    <AppShell title="Incident Detail">
      {isLoading || !data ? (
        <div className="rounded-2xl border bg-white p-8 shadow-panel">Loading incident...</div>
      ) : (
        <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <div>
                  <p className="text-xs uppercase tracking-wide text-[var(--muted)]">{data.reference}</p>
                  <CardTitle className="mt-2">{data.title}</CardTitle>
                </div>
                <div className="flex items-center gap-2">
                  <Badge tone={data.status}>{data.status}</Badge>
                  <Badge tone={data.priority === "P1" ? "critical" : data.priority === "P2" ? "high" : "medium"}>
                    {data.priority}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-[var(--muted)]">{data.summary}</p>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-2xl border px-4 py-3">
                    <p className="text-xs uppercase tracking-wide text-[var(--muted)]">Opened</p>
                    <p className="mt-2 font-semibold">{formatDate(data.opened_at)}</p>
                  </div>
                  <div className="rounded-2xl border px-4 py-3">
                    <p className="text-xs uppercase tracking-wide text-[var(--muted)]">Assignee</p>
                    <p className="mt-2 font-semibold">{data.assignee?.full_name ?? "Unassigned"}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Timeline and notes</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Textarea value={note} onChange={(event) => setNote(event.target.value)} placeholder="Add a timeline note or decision" />
                <Button onClick={() => noteMutation.mutate()} disabled={!note || noteMutation.isPending}>
                  Add note
                </Button>
                <div className="space-y-3">
                  {data.notes.map((entry) => (
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
                <CardTitle>Incident workflow</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Select value={data.status} onChange={(event) => updateMutation.mutate({ status: event.target.value })}>
                  <option value="open">Open</option>
                  <option value="contained">Contained</option>
                  <option value="monitoring">Monitoring</option>
                  <option value="resolved">Resolved</option>
                </Select>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Linked alerts</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {data.linked_alerts.map((alert) => (
                  <div key={alert.id} className="rounded-2xl border px-4 py-3">
                    <div className="flex items-center justify-between gap-3">
                      <Link className="font-semibold hover:text-[var(--accent)]" href={`/alerts/${alert.id}`}>
                        {alert.title}
                      </Link>
                      <Badge tone={alert.severity}>{alert.severity}</Badge>
                    </div>
                    <p className="mt-2 text-sm text-[var(--muted)]">{alert.source}</p>
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
