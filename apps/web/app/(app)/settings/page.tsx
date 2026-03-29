"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { EmptyState } from "@/components/feedback/empty-state";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { PageHeader } from "@/components/shared/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, createQueryString } from "@/lib/api";
import { describeLatency } from "@/lib/format";
import { isAdmin } from "@/lib/permissions";
import { useAuth } from "@/hooks/use-auth";
import type { HealthResponse, Integration, PageResult } from "@/types/domain";

export default function SettingsPage() {
  const { data: user, isLoading: isAuthLoading, isError: isAuthError, refetch: refetchAuth } = useAuth();
  const healthQuery = useQuery({
    queryKey: ["health", "settings"],
    queryFn: () => api.get<HealthResponse>("/health"),
  });
  const integrationsQuery = useQuery({
    queryKey: ["settings", "integrations"],
    queryFn: () => api.get<PageResult<Integration>>(`/integrations${createQueryString({ page: 1, page_size: 12 })}`),
  });

  if (isAuthLoading || healthQuery.isLoading || integrationsQuery.isLoading) {
    return <LoadingState lines={7} />;
  }

  if (isAuthError || !user) {
    return <ErrorState description="Session details could not be loaded." onRetry={() => refetchAuth()} />;
  }

  if (healthQuery.isError || integrationsQuery.isError || !healthQuery.data || !integrationsQuery.data) {
    return (
      <ErrorState
        description="Settings data could not be loaded from the platform services."
        onRetry={() => {
          healthQuery.refetch();
          integrationsQuery.refetch();
        }}
      />
    );
  }

  const services = [
    { label: "Application", details: healthQuery.data.app },
    { label: "Database", details: healthQuery.data.database },
    { label: "Redis", details: healthQuery.data.redis },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Platform controls"
        title="Settings"
        description="Review service health, defensive guardrails, integration posture, and the access model currently applied to your session."
        actions={<Badge tone={user.role === "Admin" ? "critical" : user.role === "Analyst" ? "high" : "medium"}>{user.role}</Badge>}
      />

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <Card>
          <CardHeader>
            <CardTitle>Service health</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-3">
            {services.map((service) => (
              <div key={service.label} className="rounded-[1.25rem] border bg-white p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-semibold text-[#111111]">{service.label}</p>
                  <Badge tone={service.details.status === "ok" ? "healthy" : "offline"}>{service.details.status}</Badge>
                </div>
                <p className="mt-4 text-sm text-[#6f6f6f]">{service.details.detail ?? "Healthy connection state."}</p>
                <p className="mt-3 text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Latency {describeLatency(service.details.latency_ms)}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Access model</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-[1.25rem] border bg-white p-4">
              <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Current role</p>
              <div className="mt-3">
                <Badge tone={user.role === "Admin" ? "critical" : user.role === "Analyst" ? "high" : "medium"}>{user.role}</Badge>
              </div>
            </div>
            <div className="rounded-[1.25rem] border bg-white p-4 text-sm leading-6 text-[#5f5f5f]">
              Administrators can manage users and audits, analysts can update alerts, incidents, and imports, and viewers remain read-only across operational workflows.
            </div>
            <div className="flex flex-wrap gap-3">
              <Button asChild variant="outline">
                <Link href="/profile">Review profile</Link>
              </Button>
              {isAdmin(user.role) ? (
                <Button asChild>
                  <Link href="/admin">Open admin controls</Link>
                </Button>
              ) : null}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <Card>
          <CardHeader>
            <CardTitle>Defensive guardrails</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm leading-6 text-[#5f5f5f]">
            <div className="rounded-[1.25rem] border bg-white p-4">JWT-backed authentication protects both HTTP requests and realtime alert streams.</div>
            <div className="rounded-[1.25rem] border bg-white p-4">Wazuh and Suricata are handled as defensive telemetry sources for alerting and log correlation.</div>
            <div className="rounded-[1.25rem] border bg-white p-4">Nmap and Hydra support is limited to safe lab-result imports only. No scanning, brute-force, or offensive execution is exposed in the UI.</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Integration posture</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {integrationsQuery.data.items.length ? (
              integrationsQuery.data.items.map((integration) => (
                <div key={integration.id} className="flex items-center justify-between gap-4 rounded-[1.25rem] border bg-white px-4 py-4">
                  <div>
                    <p className="font-semibold text-[#111111]">{integration.name}</p>
                    <p className="mt-1 text-sm text-[#6f6f6f]">{integration.description ?? "No integration description available."}</p>
                    <p className="mt-2 text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">{integration.enabled ? "Enabled" : "Disabled"} connector</p>
                  </div>
                  <Badge tone={integration.health_status}>{integration.health_status}</Badge>
                </div>
              ))
            ) : (
              <EmptyState
                title="No integrations configured"
                description="Integration status cards will appear here after the first telemetry connectors are initialized."
              />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
