"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { PageResult, User } from "@/types/domain";

type AuditLog = {
  id: string;
  action: string;
  entity_type: string;
  entity_id?: string | null;
  details: Record<string, string>;
  created_at: string;
  actor?: User | null;
};

export default function AdminPage() {
  const queryClient = useQueryClient();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState("Analyst");
  const [password, setPassword] = useState("Password123!");

  const { data: users } = useQuery({
    queryKey: ["admin-users"],
    queryFn: () => api.get<PageResult<User>>("/users"),
  });
  const { data: auditLogs } = useQuery({
    queryKey: ["admin-audit"],
    queryFn: () => api.get<PageResult<AuditLog>>("/audit-logs"),
  });
  const createUser = useMutation({
    mutationFn: () => api.post<User>("/users", { email, full_name: fullName, role, password }),
    onSuccess: () => {
      setEmail("");
      setFullName("");
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      queryClient.invalidateQueries({ queryKey: ["admin-audit"] });
    },
  });

  return (
    <AppShell title="Admin Controls">
      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <Card>
          <CardHeader>
            <CardTitle>User management</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input value={fullName} onChange={(event) => setFullName(event.target.value)} placeholder="Full name" />
            <Input value={email} onChange={(event) => setEmail(event.target.value)} placeholder="Email address" />
            <Select value={role} onChange={(event) => setRole(event.target.value)}>
              <option value="Admin">Admin</option>
              <option value="Analyst">Analyst</option>
              <option value="Viewer">Viewer</option>
            </Select>
            <Input value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Temporary password" />
            <Button onClick={() => createUser.mutate()} disabled={!email || !fullName || createUser.isPending}>
              Create user
            </Button>
            <div className="space-y-3">
              {users?.items.map((user) => (
                <div key={user.id} className="flex items-center justify-between rounded-2xl border px-4 py-3">
                  <div>
                    <p className="font-semibold">{user.full_name}</p>
                    <p className="text-sm text-[var(--muted)]">{user.email}</p>
                  </div>
                  <Badge tone={user.role === "Admin" ? "high" : user.role === "Analyst" ? "medium" : "low"}>{user.role}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Audit trail</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {auditLogs?.items.map((entry) => (
              <div key={entry.id} className="rounded-2xl border px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-semibold">{entry.action}</p>
                  <p className="text-xs uppercase tracking-wide text-[var(--muted)]">{formatDate(entry.created_at)}</p>
                </div>
                <p className="mt-2 text-sm text-[var(--muted)]">
                  {entry.actor?.full_name ?? "System"} • {entry.entity_type} {entry.entity_id ?? ""}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
