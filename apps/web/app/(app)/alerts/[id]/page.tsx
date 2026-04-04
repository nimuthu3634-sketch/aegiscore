"use client";

import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { FormField } from "@/components/forms/form-field";
import { PageHeader } from "@/components/shared/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { api, createQueryString } from "@/lib/api";
import { formatDate, scoreTone } from "@/lib/format";
import { canManageOperations } from "@/lib/permissions";
import { useAuth } from "@/hooks/use-auth";
import type { Alert, Incident, PageResult, ResponseActionResult, ResponseActionType, User } from "@/types/domain";

const commentSchema = z.object({
  body: z.string().min(2, "Add at least a short triage note."),
});

const incidentSchema = z.object({
  title: z.string().min(3, "Incident title is required."),
  description: z.string().optional(),
  assignee_id: z.string().optional(),
});

const containmentActions: Array<{ action: ResponseActionType; label: string; description: string }> = [
  {
    action: "block_ip",
    label: "Block source IP",
    description: "Record a perimeter or host firewall block for the source indicator tied to this alert.",
  },
  {
    action: "isolate_asset",
    label: "Isolate asset",
    description: "Record host isolation for the linked endpoint so the analyst can quarantine it in tooling.",
  },
  {
    action: "disable_user",
    label: "Disable user",
    description: "Record an account disable action when the alert includes affected username context.",
  },
  {
    action: "contain_alert",
    label: "Mark contained",
    description: "Move the alert into active containment handling and document the action trail.",
  },
];

export default function AlertDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: currentUser } = useAuth();
  const canManageAlert = canManageOperations(currentUser?.role);

  const alertQuery = useQuery({
    queryKey: ["alert", params.id],
    queryFn: () => api.get<Alert>(`/alerts/${params.id}`),
  });
  const usersQuery = useQuery({
    queryKey: ["users", "assignable"],
    queryFn: () => api.get<PageResult<User>>(`/users${createQueryString({ page: 1, page_size: 50 })}`),
    enabled: canManageAlert,
    retry: false,
  });

  const commentForm = useForm<z.infer<typeof commentSchema>>({
    resolver: zodResolver(commentSchema),
    defaultValues: { body: "" },
  });
  const incidentForm = useForm<z.infer<typeof incidentSchema>>({
    resolver: zodResolver(incidentSchema),
    values: {
      title: alertQuery.data ? `Investigate ${alertQuery.data.title}` : "",
      description: alertQuery.data?.description ?? "",
      assignee_id: currentUser?.id ?? "",
    },
  });

  const responseMutation = useMutation({
    mutationFn: (action: ResponseActionType) =>
      api.post<ResponseActionResult>(`/alerts/${params.id}/respond`, { action }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alert", params.id] });
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => api.patch<Alert>(`/alerts/${params.id}`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alert", params.id] });
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] });
    },
  });

  const commentMutation = useMutation({
    mutationFn: (values: z.infer<typeof commentSchema>) => api.post(`/alerts/${params.id}/comments`, values),
    onSuccess: () => {
      commentForm.reset();
      queryClient.invalidateQueries({ queryKey: ["alert", params.id] });
    },
  });

  const incidentMutation = useMutation({
    mutationFn: (values: z.infer<typeof incidentSchema>) =>
      api.post<Incident>(`/alerts/${params.id}/incident`, {
        title: values.title,
        description: values.description,
        assignee_id: values.assignee_id || undefined,
        priority:
          alertQuery.data?.severity === "critical" ? "P1" : alertQuery.data?.severity === "high" ? "P2" : "P3",
        linked_alert_ids: [params.id],
        evidence: [],
      }),
    onSuccess: (incident) => router.push(`/incidents/${incident.id}`),
  });

  if (alertQuery.isLoading) {
    return <LoadingState lines={7} />;
  }

  if (alertQuery.isError || !alertQuery.data) {
    return <ErrorState description={alertQuery.error instanceof Error ? alertQuery.error.message : "Alert could not be loaded."} onRetry={() => alertQuery.refetch()} />;
  }

  const alert = alertQuery.data;
  const assignableUsers = canManageAlert
    ? usersQuery.data?.items?.length
      ? usersQuery.data.items
      : currentUser
        ? [currentUser]
        : []
    : [];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Alert detail"
        title={alert.title}
        description={alert.description ?? "No extended description was attached to this alert."}
        badge={alert.source}
        actions={<Badge tone={scoreTone(alert.risk_score)}>Risk {alert.risk_score.toFixed(1)}</Badge>}
      />

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Alert overview</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2">
              <div className="rounded-[1.25rem] border bg-[#fcfcfc] p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Source</p>
                <p className="mt-3 font-semibold">{alert.source}</p>
                <p className="mt-1 text-sm text-[#6f6f6f]">{alert.source_type}</p>
              </div>
              <div className="rounded-[1.25rem] border bg-[#fcfcfc] p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Event type</p>
                <p className="mt-3 font-semibold">{alert.event_type ?? "Unclassified event"}</p>
                <p className="mt-1 text-sm text-[#6f6f6f]">Detected {formatDate(alert.detected_at)}</p>
              </div>
              <div className="rounded-[1.25rem] border bg-[#fcfcfc] p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Severity</p>
                <div className="mt-3 flex items-center gap-2">
                  <Badge tone={alert.severity}>{alert.severity}</Badge>
                  <Badge tone={alert.status}>{alert.status}</Badge>
                </div>
              </div>
              <div className="rounded-[1.25rem] border bg-[#fcfcfc] p-4">
                <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Asset</p>
                {alert.asset ? (
                  <Link href={`/assets/${alert.asset.id}`} className="mt-3 block font-semibold hover:text-[#FF7A1A]">
                    {alert.asset.hostname}
                  </Link>
                ) : (
                  <p className="mt-3 font-semibold">Unmapped asset</p>
                )}
                <p className="mt-1 text-sm text-[#6f6f6f]">{alert.asset?.ip_address ?? "No IP metadata available"}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Explainable risk</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="rounded-[1.25rem] border bg-[#fcfcfc] p-4 text-sm leading-6 text-[#5f5f5f]">
                {alert.explanation_summary ?? "Explainability summary was not returned for this alert."}
              </div>
              {alert.explainability.map((factor) => (
                <div key={factor.factor} className="rounded-[1.25rem] border p-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="font-semibold capitalize text-[#111111]">{factor.factor}</p>
                    <Badge tone={factor.impact > 10 ? "high" : "medium"}>Impact {factor.impact}</Badge>
                  </div>
                  {"value" in factor && factor.value !== undefined ? (
                    <p className="mt-2 text-sm text-[#6f6f6f]">Observed value: {factor.value}</p>
                  ) : null}
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Comments</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {canManageAlert ? (
                <form className="space-y-3" onSubmit={commentForm.handleSubmit((values) => commentMutation.mutate(values))}>
                  <FormField label="Add analyst note" error={commentForm.formState.errors.body?.message}>
                    <Textarea {...commentForm.register("body")} placeholder="Capture triage context, validation notes, or response decisions." />
                  </FormField>
                  <Button type="submit" disabled={commentMutation.isPending}>
                    {commentMutation.isPending ? "Saving comment..." : "Add comment"}
                  </Button>
                </form>
              ) : (
                <div className="rounded-[1.25rem] border bg-white p-4 text-sm leading-6 text-[#5f5f5f]">
                  Viewer access is read-only for alert collaboration. Analysts or administrators can add triage comments.
                </div>
              )}

              <div className="space-y-3">
                {alert.comments.length ? (
                  alert.comments.map((entry) => (
                    <div key={entry.id} className="rounded-[1.25rem] border bg-[#fcfcfc] p-4">
                      <div className="flex items-center justify-between gap-3">
                        <p className="font-semibold text-[#111111]">{entry.author?.full_name ?? "System"}</p>
                        <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">{formatDate(entry.created_at)}</p>
                      </div>
                      <p className="mt-3 text-sm leading-6 text-[#5f5f5f]">{entry.body}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-[#6f6f6f]">No analyst comments have been added yet.</p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          {canManageAlert ? (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Triage controls</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <FormField label="Status">
                    <Select
                      value={alert.status}
                      onChange={(event) => updateMutation.mutate({ status: event.target.value })}
                      disabled={updateMutation.isPending}
                    >
                      <option value="open">Open</option>
                      <option value="triaged">Triaged</option>
                      <option value="investigating">Investigating</option>
                      <option value="resolved">Resolved</option>
                      <option value="suppressed">Suppressed</option>
                    </Select>
                  </FormField>
                  <FormField label="Assign analyst">
                    <Select
                      value={alert.assignee?.id ?? ""}
                      onChange={(event) => updateMutation.mutate({ assigned_to_id: event.target.value || null })}
                      disabled={updateMutation.isPending || !assignableUsers.length}
                    >
                      <option value="">Unassigned</option>
                      {assignableUsers.map((user) => (
                        <option key={user.id} value={user.id}>
                          {user.full_name}
                        </option>
                      ))}
                    </Select>
                  </FormField>
                  <Button variant="outline" onClick={() => updateMutation.mutate({ assigned_to_id: currentUser?.id ?? null })} disabled={!currentUser}>
                    Assign to me
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Containment actions</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="rounded-[1.25rem] border bg-[#fff7f1] p-4 text-sm leading-6 text-[#8a4e16]">
                    These actions are recorded and audited inside AegisCore. They do not directly enforce firewall,
                    identity, or host controls yet, but they create a clear containment trail and leave room for future enforcement integrations.
                  </div>

                  <div className="grid gap-3">
                    {containmentActions.map((item) => (
                      <div key={item.action} className="rounded-[1.25rem] border bg-[#fcfcfc] p-4">
                        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                          <div>
                            <p className="font-semibold text-[#111111]">{item.label}</p>
                            <p className="mt-1 text-sm leading-6 text-[#5f5f5f]">{item.description}</p>
                          </div>
                          <Button
                            variant="outline"
                            onClick={() => responseMutation.mutate(item.action)}
                            disabled={responseMutation.isPending}
                          >
                            {responseMutation.isPending && responseMutation.variables === item.action ? "Recording..." : item.label}
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>

                  {responseMutation.data ? (
                    <div className="rounded-[1.25rem] border bg-white p-4">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge tone="high">{responseMutation.data.action}</Badge>
                        <Badge tone="medium">{responseMutation.data.status}</Badge>
                        <Badge tone="low">{responseMutation.data.execution_mode === "recorded" ? "Workflow action" : "Enforced action"}</Badge>
                        <span className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">
                          {formatDate(responseMutation.data.executed_at)}
                        </span>
                      </div>

                      <p className="mt-3 text-sm leading-6 text-[#5f5f5f]">{responseMutation.data.message}</p>
                      <p className="mt-2 text-xs uppercase tracking-[0.22em] text-[#8f8f8f]">
                        {responseMutation.data.execution_provider
                          ? `Provider ${responseMutation.data.execution_provider}`
                          : "Recorded for analyst follow-through"}
                      </p>

                      {Object.keys(responseMutation.data.target).length ? (
                        <div className="mt-4 grid gap-2">
                          {Object.entries(responseMutation.data.target).map(([key, value]) => (
                            <div key={key} className="flex items-center justify-between rounded-xl border px-3 py-2 text-sm">
                              <span className="capitalize text-[#6f6f6f]">{key.replaceAll("_", " ")}</span>
                              <span className="font-medium text-[#111111]">{value ?? "Unavailable"}</span>
                            </div>
                          ))}
                        </div>
                      ) : null}

                      {responseMutation.data.follow_up.length ? (
                        <div className="mt-4 space-y-2">
                          {responseMutation.data.follow_up.map((item) => (
                            <div key={item} className="rounded-xl border bg-[#fcfcfc] px-3 py-2 text-sm leading-6 text-[#5f5f5f]">
                              {item}
                            </div>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  ) : null}

                  {responseMutation.error instanceof Error ? (
                    <div className="rounded-[1.25rem] border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                      {responseMutation.error.message}
                    </div>
                  ) : null}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Create incident</CardTitle>
                </CardHeader>
                <CardContent>
                  <form className="space-y-4" onSubmit={incidentForm.handleSubmit((values) => incidentMutation.mutate(values))}>
                    <FormField label="Incident title" error={incidentForm.formState.errors.title?.message}>
                      <Input {...incidentForm.register("title")} />
                    </FormField>
                    <FormField label="Description">
                      <Textarea {...incidentForm.register("description")} className="min-h-[120px]" />
                    </FormField>
                    <FormField label="Assignee">
                      <Select {...incidentForm.register("assignee_id")}>
                        <option value="">No assignee</option>
                        {assignableUsers.map((user) => (
                          <option key={user.id} value={user.id}>
                            {user.full_name}
                          </option>
                        ))}
                      </Select>
                    </FormField>
                    <Button type="submit" disabled={incidentMutation.isPending}>
                      {incidentMutation.isPending ? "Opening incident..." : "Create incident from alert"}
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Triage access</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-6 text-[#5f5f5f]">This alert is visible in read-only mode for your role. Analysts or administrators can change status, assign ownership, and create incidents.</p>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Response recommendations</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {alert.response_recommendations.length ? (
                alert.response_recommendations
                  .sort((left, right) => left.priority - right.priority)
                  .map((item) => (
                    <div key={item.id} className="rounded-[1.25rem] border bg-[#fcfcfc] p-4">
                      <div className="flex items-center justify-between gap-3">
                        <p className="font-semibold text-[#111111]">{item.title}</p>
                        <Badge tone={item.priority <= 2 ? "high" : "medium"}>Priority {item.priority}</Badge>
                      </div>
                      <p className="mt-2 text-sm leading-6 text-[#5f5f5f]">{item.description ?? "No additional recommendation details."}</p>
                    </div>
                  ))
              ) : (
                <p className="text-sm text-[#6f6f6f]">No response recommendations are currently attached.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
