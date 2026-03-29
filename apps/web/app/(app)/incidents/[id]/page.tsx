"use client";

import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download } from "lucide-react";
import { useParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { FormField } from "@/components/forms/form-field";
import { PageHeader } from "@/components/shared/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { api, createQueryString, downloadTextFile } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { canManageOperations } from "@/lib/permissions";
import { useAuth } from "@/hooks/use-auth";
import type { Incident, PageResult, User } from "@/types/domain";

const noteSchema = z.object({
  body: z.string().min(2, "Add some timeline context before saving."),
});

export default function IncidentDetailPage() {
  const params = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const { data: currentUser } = useAuth();
  const canManageCases = canManageOperations(currentUser?.role);

  const incidentQuery = useQuery({
    queryKey: ["incident", params.id],
    queryFn: () => api.get<Incident>(`/incidents/${params.id}`),
  });
  const usersQuery = useQuery({
    queryKey: ["users", "incident-detail"],
    queryFn: () => api.get<PageResult<User>>(`/users${createQueryString({ page: 1, page_size: 50 })}`),
  });

  const noteForm = useForm<z.infer<typeof noteSchema>>({
    resolver: zodResolver(noteSchema),
    defaultValues: { body: "" },
  });

  const updateMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => api.patch<Incident>(`/incidents/${params.id}`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["incident", params.id] });
      queryClient.invalidateQueries({ queryKey: ["incidents"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] });
    },
  });

  const noteMutation = useMutation({
    mutationFn: (values: z.infer<typeof noteSchema>) =>
      api.post(`/incidents/${params.id}/events`, {
        body: values.body,
        event_type: "note",
        is_timeline_event: true,
        event_metadata: {},
      }),
    onSuccess: () => {
      noteForm.reset();
      queryClient.invalidateQueries({ queryKey: ["incident", params.id] });
    },
  });

  if (incidentQuery.isLoading) {
    return <LoadingState lines={8} />;
  }

  if (incidentQuery.isError || !incidentQuery.data) {
    return <ErrorState description={incidentQuery.error instanceof Error ? incidentQuery.error.message : "Incident could not be loaded."} onRetry={() => incidentQuery.refetch()} />;
  }

  const incident = incidentQuery.data;
  const assignableUsers = usersQuery.data?.items?.length ? usersQuery.data.items : currentUser ? [currentUser] : [];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Incident detail"
        title={`${incident.reference}: ${incident.title}`}
        description={incident.description ?? "No case summary has been recorded yet."}
        actions={
          <Button
            variant="outline"
            onClick={async () =>
              downloadTextFile(
                `${incident.reference.toLowerCase()}.txt`,
                await api.get<string>(`/reports/incidents/${incident.id}/summary`),
                "text/plain",
              )
            }
          >
            <Download className="mr-2 h-4 w-4" />
            Export summary
          </Button>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Case overview</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2">
              <div className="rounded-[1.25rem] border bg-[#fcfcfc] p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Status</p>
                <div className="mt-3">
                  <Badge tone={incident.status}>{incident.status}</Badge>
                </div>
              </div>
              <div className="rounded-[1.25rem] border bg-[#fcfcfc] p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Priority</p>
                <div className="mt-3">
                  <Badge tone={incident.priority === "P1" ? "critical" : incident.priority === "P2" ? "high" : "medium"}>{incident.priority}</Badge>
                </div>
              </div>
              <div className="rounded-[1.25rem] border bg-[#fcfcfc] p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Opened</p>
                <p className="mt-3 font-semibold">{formatDate(incident.opened_at)}</p>
              </div>
              <div className="rounded-[1.25rem] border bg-[#fcfcfc] p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Resolved</p>
                <p className="mt-3 font-semibold">{formatDate(incident.resolved_at)}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Timeline</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {canManageCases ? (
                <form className="space-y-3" onSubmit={noteForm.handleSubmit((values) => noteMutation.mutate(values))}>
                  <FormField label="Add timeline note" error={noteForm.formState.errors.body?.message}>
                    <Textarea {...noteForm.register("body")} placeholder="Record analyst decisions, evidence, containment steps, or escalation updates." />
                  </FormField>
                  <Button type="submit" disabled={noteMutation.isPending}>
                    {noteMutation.isPending ? "Saving note..." : "Add note"}
                  </Button>
                </form>
              ) : (
                <div className="rounded-[1.25rem] border bg-white p-4 text-sm leading-6 text-[#5f5f5f]">
                  Viewer access is read-only for incident timelines. Timeline entries can be added by analysts or administrators.
                </div>
              )}

              <div className="space-y-3">
                {incident.timeline_events.map((event) => (
                  <div key={event.id} className="rounded-[1.25rem] border bg-[#fcfcfc] p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <Badge tone={event.event_type === "status-change" ? "medium" : "low"}>{event.event_type}</Badge>
                        <span className="text-sm font-medium text-[#111111]">{event.author?.full_name ?? "System"}</span>
                      </div>
                      <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">{formatDate(event.created_at)}</p>
                    </div>
                    <p className="mt-3 text-sm leading-6 text-[#5f5f5f]">{event.body}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          {canManageCases ? (
            <Card>
              <CardHeader>
                <CardTitle>Workflow controls</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <FormField label="Status">
                  <Select value={incident.status} onChange={(event) => updateMutation.mutate({ status: event.target.value })}>
                    <option value="open">Open</option>
                    <option value="contained">Contained</option>
                    <option value="monitoring">Monitoring</option>
                    <option value="resolved">Resolved</option>
                  </Select>
                </FormField>

                <FormField label="Priority">
                  <Select value={incident.priority} onChange={(event) => updateMutation.mutate({ priority: event.target.value })}>
                    <option value="P1">P1</option>
                    <option value="P2">P2</option>
                    <option value="P3">P3</option>
                    <option value="P4">P4</option>
                  </Select>
                </FormField>

                <FormField label="Assignee">
                  <Select value={incident.assignee?.id ?? ""} onChange={(event) => updateMutation.mutate({ assignee_id: event.target.value || null })}>
                    <option value="">Unassigned</option>
                    {assignableUsers.map((user) => (
                      <option key={user.id} value={user.id}>
                        {user.full_name}
                      </option>
                    ))}
                  </Select>
                </FormField>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Workflow access</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-6 text-[#5f5f5f]">This incident is visible in read-only mode for your role. Analysts or administrators can update status, priority, and assignment.</p>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Linked alerts</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {incident.linked_alerts.map((alert) => (
                <Link key={alert.id} href={`/alerts/${alert.id}`} className="block rounded-[1.25rem] border bg-[#fcfcfc] p-4 transition hover:border-[#FF7A1A]">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-semibold text-[#111111]">{alert.title}</p>
                      <p className="mt-1 text-sm text-[#6f6f6f]">{alert.source}</p>
                    </div>
                    <Badge tone={alert.severity}>{alert.severity}</Badge>
                  </div>
                </Link>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Resolution notes</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-6 text-[#5f5f5f]">
                {incident.resolution_notes ?? "Resolution notes will appear here once the incident is closed or updated."}
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
