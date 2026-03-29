"use client";

import { useQuery } from "@tanstack/react-query";

import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { Integration, PageResult } from "@/types/domain";

export default function SettingsPage() {
  const { data } = useQuery({
    queryKey: ["settings-integrations"],
    queryFn: () => api.get<PageResult<Integration>>("/integrations"),
  });

  return (
    <AppShell title="Settings">
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Platform defaults</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="rounded-2xl border px-4 py-3">JWT-backed authentication with role-based access control.</div>
            <div className="rounded-2xl border px-4 py-3">Realtime alert notifications use authenticated websocket channels.</div>
            <div className="rounded-2xl border px-4 py-3">Imports are defensive and file-based only. No scan or brute-force execution exists in the product.</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Integration state</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {data?.items.map((integration) => (
              <div key={integration.id} className="flex items-center justify-between rounded-2xl border px-4 py-3">
                <div>
                  <p className="font-semibold">{integration.name}</p>
                  <p className="text-sm text-[var(--muted)]">{integration.description}</p>
                </div>
                <Badge tone={integration.health_status}>{integration.health_status}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
