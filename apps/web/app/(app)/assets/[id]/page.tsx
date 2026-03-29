"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { Alert, Asset, Incident, PageResult } from "@/types/domain";

export default function AssetDetailPage() {
  const params = useParams<{ id: string }>();
  const { data: asset } = useQuery({ queryKey: ["asset", params.id], queryFn: () => api.get<Asset>(`/assets/${params.id}`) });
  const { data: alerts } = useQuery({ queryKey: ["asset-alerts"], queryFn: () => api.get<PageResult<Alert>>("/alerts") });
  const { data: incidents } = useQuery({ queryKey: ["asset-incidents"], queryFn: () => api.get<PageResult<Incident>>("/incidents") });

  const linkedAlerts = alerts?.items.filter((alert) => alert.asset?.id === params.id) ?? [];
  const linkedIncidents =
    incidents?.items.filter((incident) => incident.linked_alerts.some((alert) => alert.asset?.id === params.id)) ?? [];

  return (
    <AppShell title="Asset Detail">
      {!asset ? (
        <div className="rounded-2xl border bg-white p-8 shadow-panel">Loading asset...</div>
      ) : (
        <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          <Card>
            <CardHeader>
              <div>
                <CardTitle>{asset.hostname}</CardTitle>
                <p className="mt-2 text-sm text-[var(--muted)]">{asset.operating_system ?? "OS not provided"}</p>
              </div>
              <Badge tone={asset.risk_score >= 65 ? "high" : asset.risk_score >= 35 ? "medium" : "low"}>{asset.risk_score}</Badge>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-2xl border px-4 py-3">
                  <p className="text-xs uppercase tracking-wide text-[var(--muted)]">IP address</p>
                  <p className="mt-2 font-semibold">{asset.ip_address ?? "Unknown"}</p>
                </div>
                <div className="rounded-2xl border px-4 py-3">
                  <p className="text-xs uppercase tracking-wide text-[var(--muted)]">Last seen</p>
                  <p className="mt-2 font-semibold">{formatDate(asset.last_seen_at)}</p>
                </div>
              </div>
              <div className="rounded-2xl border px-4 py-3 text-sm">{asset.risk_summary ?? "No current risk summary"}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Linked alerts</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {linkedAlerts.map((alert) => (
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
          <Card className="xl:col-span-2">
            <CardHeader>
              <CardTitle>Related incidents</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-2">
              {linkedIncidents.map((incident) => (
                <div key={incident.id} className="rounded-2xl border px-4 py-3">
                  <div className="flex items-center justify-between gap-3">
                    <Link className="font-semibold hover:text-[var(--accent)]" href={`/incidents/${incident.id}`}>
                      {incident.reference}
                    </Link>
                    <Badge tone={incident.status}>{incident.status}</Badge>
                  </div>
                  <p className="mt-2 text-sm text-[var(--muted)]">{incident.title}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      )}
    </AppShell>
  );
}
