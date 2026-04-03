"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { type ColumnDef } from "@tanstack/react-table";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useDeferredValue, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { EmptyState } from "@/components/feedback/empty-state";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { FormField } from "@/components/forms/form-field";
import { PageHeader } from "@/components/shared/page-header";
import { PaginationControls } from "@/components/shared/pagination-controls";
import { StatCard } from "@/components/shared/stat-card";
import { DataTable } from "@/components/tables/data-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { api, createQueryString } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { isAdmin } from "@/lib/permissions";
import { passwordPolicyHint, strongPasswordSchema } from "@/lib/validation";
import { useAuth } from "@/hooks/use-auth";
import type { AuditLog, PageResult, Role, User } from "@/types/domain";

const userSchema = z.object({
  full_name: z.string().trim().min(2, "Full name is required."),
  email: z.string().email("Enter a valid email address."),
  role: z.enum(["Admin", "Analyst", "Viewer"]),
  password: strongPasswordSchema("Temporary password"),
});

function roleTone(role: Role) {
  if (role === "Admin") {
    return "critical";
  }
  if (role === "Analyst") {
    return "high";
  }
  return "medium";
}

export default function AdminPage() {
  const queryClient = useQueryClient();
  const { data: currentUser, isLoading: isAuthLoading, isError: isAuthError, refetch: refetchAuth } = useAuth();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [activeFilter, setActiveFilter] = useState("");
  const deferredSearch = useDeferredValue(search);
  const adminAccess = isAdmin(currentUser?.role);

  const form = useForm<z.infer<typeof userSchema>>({
    resolver: zodResolver(userSchema),
    defaultValues: {
      full_name: "",
      email: "",
      role: "Analyst",
      password: "Password123!",
    },
  });

  const usersQuery = useQuery({
    queryKey: ["admin", "users", page, deferredSearch, roleFilter, activeFilter],
    queryFn: () =>
      api.get<PageResult<User>>(
        `/users${createQueryString({
          page,
          page_size: 12,
          q: deferredSearch,
          role: roleFilter,
          is_active: activeFilter === "" ? undefined : activeFilter === "true",
        })}`,
      ),
    enabled: adminAccess,
  });

  const auditQuery = useQuery({
    queryKey: ["admin", "audit"],
    queryFn: () => api.get<PageResult<AuditLog>>(`/audit-logs${createQueryString({ page: 1, page_size: 8 })}`),
    enabled: adminAccess,
  });

  const createMutation = useMutation({
    mutationFn: (values: z.infer<typeof userSchema>) => api.post<User>("/users", values),
    onSuccess: () => {
      form.reset({
        full_name: "",
        email: "",
        role: "Analyst",
        password: "Password123!",
      });
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "audit"] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ userId, payload }: { userId: string; payload: Partial<Pick<User, "role" | "is_active">> & { password?: string } }) =>
      api.patch<User>(`/users/${userId}`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "audit"] });
    },
  });

  const summary = useMemo(
    () => {
      const displayedUsers = usersQuery.data?.items ?? [];
      return {
        total: usersQuery.data?.total ?? 0,
        admins: displayedUsers.filter((user) => user.role === "Admin").length,
        analysts: displayedUsers.filter((user) => user.role === "Analyst").length,
        inactive: displayedUsers.filter((user) => !user.is_active).length,
      };
    },
    [usersQuery.data],
  );

  const columns: ColumnDef<User>[] = [
    {
      accessorKey: "full_name",
      header: "User",
      cell: ({ row }) => (
        <div className="space-y-1">
          <p className="font-semibold text-[#111111]">{row.original.full_name}</p>
          <p className="text-sm text-[#6f6f6f]">{row.original.email}</p>
        </div>
      ),
    },
    {
      accessorKey: "role",
      header: "Role",
      cell: ({ row }) => (
        <Select
          value={row.original.role}
          onChange={(event) => updateMutation.mutate({ userId: row.original.id, payload: { role: event.target.value as Role } })}
          disabled={updateMutation.isPending || row.original.id === currentUser?.id}
          className="min-w-[132px]"
          aria-label={`Role for ${row.original.full_name || row.original.email}`}
        >
          <option value="Admin">Admin</option>
          <option value="Analyst">Analyst</option>
          <option value="Viewer">Viewer</option>
        </Select>
      ),
    },
    {
      accessorKey: "is_active",
      header: "Status",
      cell: ({ row }) => <Badge tone={row.original.is_active ? "healthy" : "offline"}>{row.original.is_active ? "Active" : "Inactive"}</Badge>,
    },
    {
      accessorKey: "last_login_at",
      header: "Last login",
      cell: ({ row }) => formatDate(row.original.last_login_at),
    },
    {
      id: "actions",
      header: "Action",
      cell: ({ row }) =>
        row.original.id === currentUser?.id ? (
          <Badge tone="medium">Current session</Badge>
        ) : (
          <Button
            variant="outline"
            size="sm"
            onClick={() => updateMutation.mutate({ userId: row.original.id, payload: { is_active: !row.original.is_active } })}
            disabled={updateMutation.isPending}
          >
            {row.original.is_active ? "Deactivate" : "Restore"}
          </Button>
        ),
    },
  ];

  if (isAuthLoading) {
    return <LoadingState lines={6} />;
  }

  if (isAuthError || !currentUser) {
    return <ErrorState description="Current session details could not be loaded." onRetry={() => refetchAuth()} />;
  }

  if (!adminAccess) {
    return (
      <div className="space-y-6">
        <PageHeader
          eyebrow="Administration"
          title="Admin / Users"
          description="Only administrators can manage user accounts and review the full audit trail."
        />
        <EmptyState
          title="Administrator access required"
          description="Your current role is read-only for user administration. Sign in as an administrator to create accounts, change roles, or inspect audit records."
        />
      </div>
    );
  }

  if (usersQuery.isLoading || auditQuery.isLoading) {
    return <LoadingState lines={8} />;
  }

  if (usersQuery.isError || auditQuery.isError || !usersQuery.data || !auditQuery.data) {
    return (
      <ErrorState
        description="Admin data could not be loaded from the API."
        onRetry={() => {
          usersQuery.refetch();
          auditQuery.refetch();
        }}
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Administration"
        title="Admin / Users"
        description="Manage analyst access, review account status, and keep an audit trail of privileged actions across the AegisCore workspace."
        actions={<Badge tone="critical">Admin only</Badge>}
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Directory size" value={String(summary.total)} detail="Total user accounts" tone="healthy" />
        <StatCard label="Admins on page" value={String(summary.admins)} detail="Privileged operators in current view" tone="critical" />
        <StatCard label="Analysts on page" value={String(summary.analysts)} detail="Operational analysts in current view" tone="high" />
        <StatCard label="Inactive on page" value={String(summary.inactive)} detail="Accounts currently suspended" />
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Create user</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={form.handleSubmit((values) => createMutation.mutate(values))}>
              <FormField label="Full name" error={form.formState.errors.full_name?.message}>
                <Input {...form.register("full_name")} placeholder="AegisCore Analyst" />
              </FormField>
              <FormField label="Email address" error={form.formState.errors.email?.message}>
                <Input {...form.register("email")} placeholder="analyst@example.com" />
              </FormField>
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField label="Role" error={form.formState.errors.role?.message}>
                  <Select {...form.register("role")} aria-label="User role">
                    <option value="Admin">Admin</option>
                    <option value="Analyst">Analyst</option>
                    <option value="Viewer">Viewer</option>
                  </Select>
                </FormField>
                <FormField label="Temporary password" hint={passwordPolicyHint} error={form.formState.errors.password?.message}>
                  <Input {...form.register("password")} type="password" placeholder="Password123!" />
                </FormField>
              </div>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? "Creating account..." : "Create user"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardContent className="grid gap-3 lg:grid-cols-[1.4fr_repeat(2,minmax(0,1fr))]">
              <Input
                value={search}
                onChange={(event) => {
                  setPage(1);
                  setSearch(event.target.value);
                }}
                placeholder="Search name or email"
              />
              <Select
                value={roleFilter}
                onChange={(event) => {
                  setPage(1);
                  setRoleFilter(event.target.value);
                }}
                aria-label="Filter by role"
              >
                <option value="">All roles</option>
                <option value="Admin">Admin</option>
                <option value="Analyst">Analyst</option>
                <option value="Viewer">Viewer</option>
              </Select>
              <Select
                value={activeFilter}
                onChange={(event) => {
                  setPage(1);
                  setActiveFilter(event.target.value);
                }}
                aria-label="Filter by status"
              >
                <option value="">All statuses</option>
                <option value="true">Active</option>
                <option value="false">Inactive</option>
              </Select>
            </CardContent>
          </Card>

          <DataTable
            columns={columns}
            rows={usersQuery.data.items}
            emptyTitle="No users matched the current filters"
            emptyMessage="Try widening the search, role, or status filters."
          />
          <PaginationControls
            page={usersQuery.data.page}
            pageSize={usersQuery.data.page_size}
            total={usersQuery.data.total}
            onPageChange={setPage}
          />
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent audit trail</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3">
          {auditQuery.data.items.length ? (
            auditQuery.data.items.map((entry) => (
              <div key={entry.id} className="rounded-[1.25rem] border bg-white p-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge tone={entry.actor?.role ? roleTone(entry.actor.role) : "medium"}>{entry.actor?.role ?? "System"}</Badge>
                      <p className="font-semibold text-[#111111]">{entry.action}</p>
                    </div>
                    <p className="text-sm text-[#6f6f6f]">
                      {entry.actor?.full_name ?? "System"} updated {entry.entity_type}
                      {entry.entity_id ? ` ${entry.entity_id}` : ""}.
                    </p>
                  </div>
                  <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">{formatDate(entry.created_at)}</p>
                </div>
              </div>
            ))
          ) : (
            <EmptyState
              title="No audit entries yet"
              description="Privileged actions such as user creation, updates, and workflow changes will appear here."
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
