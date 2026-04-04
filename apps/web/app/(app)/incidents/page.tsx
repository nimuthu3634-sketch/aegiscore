"use client";

import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { type ColumnDef } from "@tanstack/react-table";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useDeferredValue, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { FormField } from "@/components/forms/form-field";
import { PageHeader } from "@/components/shared/page-header";
import { PaginationControls } from "@/components/shared/pagination-controls";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { DataTable } from "@/components/tables/data-table";
import { api, createQueryString } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { canManageOperations } from "@/lib/permissions";
import { useAuth } from "@/hooks/use-auth";
import type { Incident, PageResult, User } from "@/types/domain";

const incidentSchema = z.object({
  title: z.string().min(3, "Incident title is required."),
  description: z.string().optional(),
  priority: z.enum(["P1", "P2", "P3", "P4"]),
  assignee_id: z.string().optional(),
});

const columns: ColumnDef<Incident>[] = [
  {
    accessorKey: "reference",
    header: "Incident",
    cell: ({ row }) => (
      <div className="space-y-1">
        <Link href={`/incidents/${row.original.id}`} className="font-semibold text-[#111111] hover:text-[#FF7A1A]">
          {row.original.reference}
        </Link>
        <p className="text-sm text-[#6f6f6f]">{row.original.title}</p>
      </div>
    ),
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => <Badge tone={row.original.status}>{row.original.status}</Badge>,
  },
  {
    accessorKey: "priority",
    header: "Priority",
    cell: ({ row }) => <Badge tone={row.original.priority === "P1" ? "critical" : row.original.priority === "P2" ? "high" : "medium"}>{row.original.priority}</Badge>,
  },
  {
    accessorKey: "assignee",
    header: "Assignee",
    cell: ({ row }) => row.original.assignee?.full_name ?? "Unassigned",
  },
  {
    accessorKey: "linked_alerts",
    header: "Linked alerts",
    cell: ({ row }) => <span className="font-medium">{row.original.linked_alerts.length}</span>,
  },
  {
    accessorKey: "opened_at",
    header: "Opened",
    cell: ({ row }) => formatDate(row.original.opened_at),
  },
];

export default function IncidentsPage() {
  const queryClient = useQueryClient();
  const { data: currentUser } = useAuth();
  const canManageCases = canManageOperations(currentUser?.role);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [priority, setPriority] = useState("");
  const [assigneeId, setAssigneeId] = useState("");
  const deferredSearch = useDeferredValue(search);

  const form = useForm<z.infer<typeof incidentSchema>>({
    resolver: zodResolver(incidentSchema),
    defaultValues: {
      title: "",
      description: "",
      priority: "P3",
      assignee_id: currentUser?.id ?? "",
    },
  });

  const incidentsQuery = useQuery({
    queryKey: ["incidents", page, deferredSearch, status, priority, assigneeId],
    queryFn: () =>
      api.get<PageResult<Incident>>(
        `/incidents${createQueryString({
          page,
          page_size: 12,
          q: deferredSearch,
          status,
          priority,
          assignee_id: assigneeId,
        })}`,
      ),
  });
  const usersQuery = useQuery({
    queryKey: ["users", "incident-assignees"],
    queryFn: () => api.get<PageResult<User>>(`/users${createQueryString({ page: 1, page_size: 50 })}`),
    enabled: canManageCases,
    retry: false,
  });

  const createMutation = useMutation({
    mutationFn: (values: z.infer<typeof incidentSchema>) =>
      api.post<Incident>("/incidents", {
        title: values.title,
        description: values.description,
        priority: values.priority,
        assignee_id: values.assignee_id || undefined,
        linked_alert_ids: [],
        evidence: [],
      }),
    onSuccess: () => {
      form.reset({ title: "", description: "", priority: "P3", assignee_id: currentUser?.id ?? "" });
      queryClient.invalidateQueries({ queryKey: ["incidents"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] });
    },
  });

  const assignableUsers = canManageCases
    ? usersQuery.data?.items?.length
      ? usersQuery.data.items
      : currentUser
        ? [currentUser]
        : []
    : [];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Case management"
        title="Incidents"
        description="Create, track, and resolve incidents with structured priorities, timeline notes, linked alerts, and export-ready summaries."
        actions={!canManageCases ? <Badge tone="medium">Read-only access</Badge> : undefined}
      />

      <div className={canManageCases ? "grid gap-6 xl:grid-cols-[0.9fr_1.1fr]" : "space-y-4"}>
        {canManageCases ? (
          <Card>
            <CardHeader>
              <CardTitle>Create incident</CardTitle>
            </CardHeader>
            <CardContent>
              <form className="space-y-4" onSubmit={form.handleSubmit((values) => createMutation.mutate(values))}>
                <FormField label="Title" error={form.formState.errors.title?.message}>
                  <Input {...form.register("title")} placeholder="Credential abuse investigation" />
                </FormField>
                <FormField label="Description">
                  <Textarea {...form.register("description")} placeholder="Summarize what triggered the case and what the team needs to verify next." />
                </FormField>
                <div className="grid gap-4 sm:grid-cols-2">
                  <FormField label="Priority">
                    <Select {...form.register("priority")}>
                      <option value="P1">P1</option>
                      <option value="P2">P2</option>
                      <option value="P3">P3</option>
                      <option value="P4">P4</option>
                    </Select>
                  </FormField>
                  <FormField label="Assignee">
                    <Select {...form.register("assignee_id")}>
                      <option value="">No assignee</option>
                      {assignableUsers.map((user) => (
                        <option key={user.id} value={user.id}>
                          {user.full_name}
                        </option>
                      ))}
                    </Select>
                  </FormField>
                </div>
                <Button type="submit" disabled={createMutation.isPending}>
                  {createMutation.isPending ? "Creating incident..." : "Create incident"}
                </Button>
              </form>
            </CardContent>
          </Card>
        ) : null}

        <div className="space-y-4">
          <Card>
            <CardContent className="grid gap-3 lg:grid-cols-[1.4fr_repeat(3,minmax(0,1fr))]">
              <Input value={search} onChange={(event) => { setPage(1); setSearch(event.target.value); }} placeholder="Search title or description" />
              <Select value={status} onChange={(event) => { setPage(1); setStatus(event.target.value); }}>
                <option value="">All statuses</option>
                <option value="open">Open</option>
                <option value="contained">Contained</option>
                <option value="monitoring">Monitoring</option>
                <option value="resolved">Resolved</option>
              </Select>
              <Select value={priority} onChange={(event) => { setPage(1); setPriority(event.target.value); }}>
                <option value="">All priorities</option>
                <option value="P1">P1</option>
                <option value="P2">P2</option>
                <option value="P3">P3</option>
                <option value="P4">P4</option>
              </Select>
              <Select value={assigneeId} onChange={(event) => { setPage(1); setAssigneeId(event.target.value); }}>
                <option value="">All assignees</option>
                {assignableUsers.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.full_name}
                  </option>
                ))}
              </Select>
            </CardContent>
          </Card>

          {incidentsQuery.isLoading ? (
            <LoadingState lines={7} compact />
          ) : incidentsQuery.isError || !incidentsQuery.data ? (
            <ErrorState description={incidentsQuery.error instanceof Error ? incidentsQuery.error.message : "Incidents could not be loaded."} onRetry={() => incidentsQuery.refetch()} />
          ) : (
            <>
              <DataTable
                columns={columns}
                rows={incidentsQuery.data.items}
                emptyTitle="No incidents yet"
                emptyMessage="Create the first incident or broaden the current filters."
              />
              <PaginationControls page={incidentsQuery.data.page} pageSize={incidentsQuery.data.page_size} total={incidentsQuery.data.total} onPageChange={setPage} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
