"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { PageHeader } from "@/components/shared/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, createQueryString } from "@/lib/api";
import { formatDate, scoreTone } from "@/lib/format";
import type { Alert, Asset, Incident, PageResult } from "@/types/domain";

export default function AssetDetailPage() {
  const params = useParams<{ id: string }>();
  const assetQuery = useQuery({
    queryKey: ["asset", params.id],
    queryFn: () => api.get<Asset>(`/assets/${params.id}`),
  });
  const alertsQuery = useQuery({
    queryKey: ["alerts", "asset-detail", params.id],
    queryFn: () => api.get<PageResult<Alert>>(`/alerts${createQueryString({ asset_id: params.id, page: 1, page_size: 100 })}`),
  });
  const incidentsQuery = useQuery({
    queryKey: ["incidents", "asset-detail", params.id],
    queryFn: () => api.get<PageResult<Incident>>(`/incidents${createQueryString({ linked_asset_id: params.id, page: 1, page_size: 100 })}`),
  });

  if (assetQuery.isLoading) {
    return <LoadingState lines={6} />;
  }

  if (assetQuery.isError || !assetQuery.data) {
    return <ErrorState description={assetQuery.error instanceof Error ? assetQuery.error.message : "Asset could not be loaded."} onRetry={() => assetQuery.refetch()} />;
  }

  const asset = assetQuery.data;
  const linkedAlerts = alertsQuery.data?.items ?? [];
  const linkedIncidents = incidentsQuery.data?.items ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Asset detail"
        title={asset.hostname}
        description={asset.risk_summary ?? "This asset does not yet have a detailed risk narrative."}
        actions={<Badge tone={scoreTone(asset.risk_score)}>Risk {asset.risk_score.toFixed(1)}</Badge>}
      />

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <Card>
          <CardHeader>
            <CardTitle>Host overview</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div className="rounded-[1.25rem] border bg-[#fcfcfc] p-4">
              <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">IP address</p>
              <p className="mt-3 font-semibold">{asset.ip_address ?? "Unknown"}</p>
            </div>
            <div className="rounded-[1.25rem] border bg-[#fcfcfc] p-4">
              <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Operating system</p>
              <p className="mt-3 font-semibold">{asset.operating_system ?? "Unknown"}</p>
            </div>
            <div className="rounded-[1.25rem] border bg-[#fcfcfc] p-4">
              <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Criticality</p>
              <p className="mt-3 font-semibold">{asset.criticality}</p>
            </div>
            <div className="rounded-[1.25rem] border bg-[#fcfcfc] p-4">
              <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Last seen</p>
              <p className="mt-3 font-semibold">{formatDate(asset.last_seen_at)}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Related alerts</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {alertsQuery.isLoading ? (
              <p className="text-sm text-[#6f6f6f]">Loading alerts linked to this asset...</p>
            ) : alertsQuery.isError ? (
              <div className="space-y-3 rounded-[1.25rem] border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                <p>{alertsQuery.error instanceof Error ? alertsQuery.error.message : "Related alerts could not be loaded."}</p>
                <Button type="button" variant="outline" size="sm" onClick={() => alertsQuery.refetch()}>
                  Retry alerts
                </Button>
              </div>
            ) : linkedAlerts.length ? (
              linkedAlerts.map((alert) => (
                <Link key={alert.id} href={`/alerts/${alert.id}`} className="block rounded-[1.25rem] border bg-[#fcfcfc] p-4 transition hover:border-[#FF7A1A]">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-semibold text-[#111111]">{alert.title}</p>
                      <p className="mt-1 text-sm text-[#6f6f6f]">{alert.source}</p>
                    </div>
                    <Badge tone={alert.severity}>{alert.severity}</Badge>
                  </div>
                </Link>
              ))
            ) : (
              <p className="text-sm text-[#6f6f6f]">No alerts are currently linked to this asset.</p>
            )}
          </CardContent>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>Related incidents</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2">
            {incidentsQuery.isLoading ? (
              <p className="text-sm text-[#6f6f6f] md:col-span-2">Loading incidents linked to this asset...</p>
            ) : incidentsQuery.isError ? (
              <div className="space-y-3 rounded-[1.25rem] border border-red-200 bg-red-50 p-4 text-sm text-red-700 md:col-span-2">
                <p>{incidentsQuery.error instanceof Error ? incidentsQuery.error.message : "Related incidents could not be loaded."}</p>
                <Button type="button" variant="outline" size="sm" onClick={() => incidentsQuery.refetch()}>
                  Retry incidents
                </Button>
              </div>
            ) : linkedIncidents.length ? (
              linkedIncidents.map((incident) => (
                <Link key={incident.id} href={`/incidents/${incident.id}`} className="block rounded-[1.25rem] border bg-[#fcfcfc] p-4 transition hover:border-[#FF7A1A]">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-semibold text-[#111111]">{incident.reference}</p>
                      <p className="mt-1 text-sm text-[#6f6f6f]">{incident.title}</p>
                    </div>
                    <Badge tone={incident.status}>{incident.status}</Badge>
                  </div>
                </Link>
              ))
            ) : (
              <p className="text-sm text-[#6f6f6f]">No incidents currently reference alerts on this asset.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
