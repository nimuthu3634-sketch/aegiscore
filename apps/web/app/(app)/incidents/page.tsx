"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { DataTable } from "@/components/tables/data-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { Incident, PageResult } from "@/types/domain";

export default function IncidentsPage() {
  const [title, setTitle] = useState("");
  const [summary, setSummary] = useState("");
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["incidents"],
    queryFn: () => api.get<PageResult<Incident>>("/incidents"),
  });
  const createMutation = useMutation({
    mutationFn: () =>
      api.post<Incident>("/incidents", {
        title,
        summary,
        priority: "P3",
        linked_alert_ids: [],
        evidence: [],
      }),
    onSuccess: () => {
      setTitle("");
      setSummary("");
      queryClient.invalidateQueries({ queryKey: ["incidents"] });
    },
  });

  return (
    <AppShell title="Incidents">
      <div className="space-y-6">
        <div className="grid gap-4 rounded-2xl border bg-white p-4 shadow-panel lg:grid-cols-[1fr_1.5fr_auto]">
          <Input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Create a new incident title" />
          <Textarea className="min-h-[44px]" value={summary} onChange={(event) => setSummary(event.target.value)} placeholder="Short incident summary" />
          <Button onClick={() => createMutation.mutate()} disabled={!title || createMutation.isPending}>
            Create incident
          </Button>
        </div>
        {isLoading || !data ? (
          <div className="rounded-2xl border bg-white p-8 shadow-panel">Loading incidents...</div>
        ) : (
          <DataTable
            rows={data.items}
            emptyMessage="No incidents available yet."
            columns={[
              {
                key: "reference",
                header: "Incident",
                render: (incident) => (
                  <div>
                    <Link className="font-semibold hover:text-[var(--accent)]" href={`/incidents/${incident.id}`}>
                      {incident.reference}
                    </Link>
                    <p className="mt-1 text-sm text-[var(--muted)]">{incident.title}</p>
                  </div>
                ),
              },
              {
                key: "status",
                header: "Status",
                render: (incident) => <Badge tone={incident.status}>{incident.status}</Badge>,
              },
              {
                key: "priority",
                header: "Priority",
                render: (incident) => <Badge tone={incident.priority === "P1" ? "critical" : incident.priority === "P2" ? "high" : "medium"}>{incident.priority}</Badge>,
              },
              {
                key: "assignee",
                header: "Assignee",
                render: (incident) => incident.assignee?.full_name ?? "Unassigned",
              },
              {
                key: "opened",
                header: "Opened",
                render: (incident) => formatDate(incident.opened_at),
              },
            ]}
          />
        )}
      </div>
    </AppShell>
  );
}
