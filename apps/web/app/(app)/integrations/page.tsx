"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { Integration, PageResult } from "@/types/domain";

type ImportResult = {
  integration: string;
  run_id: string;
  alerts_created: number;
  logs_created: number;
  assets_touched: number;
  incident_candidates: number;
};

export default function IntegrationsPage() {
  const [selectedIntegration, setSelectedIntegration] = useState("wazuh");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["integrations"],
    queryFn: () => api.get<PageResult<Integration>>("/integrations"),
  });

  const importMutation = useMutation({
    mutationFn: () => {
      if (!selectedFile) {
        throw new Error("Select a file to import");
      }
      return api.upload<ImportResult>(`/integrations/${selectedIntegration}/import`, selectedFile);
    },
    onSuccess: () => {
      setSelectedFile(null);
      queryClient.invalidateQueries({ queryKey: ["integrations"] });
    },
  });

  return (
    <AppShell title="Integrations">
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Import defensive telemetry</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 lg:grid-cols-[220px_1fr_auto]">
            <Select value={selectedIntegration} onChange={(event) => setSelectedIntegration(event.target.value)}>
              <option value="wazuh">Wazuh</option>
              <option value="suricata">Suricata</option>
              <option value="nmap">Nmap import</option>
              <option value="hydra">Hydra import</option>
            </Select>
            <input
              className="rounded-xl border bg-white px-3 py-2 text-sm"
              type="file"
              accept=".json"
              onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
            />
            <Button onClick={() => importMutation.mutate()} disabled={!selectedFile || importMutation.isPending}>
              {importMutation.isPending ? "Importing..." : "Import file"}
            </Button>
          </CardContent>
        </Card>

        {isLoading || !data ? (
          <div className="rounded-2xl border bg-white p-8 shadow-panel">Loading integrations...</div>
        ) : (
          <div className="grid gap-6 xl:grid-cols-2">
            {data.items.map((integration) => (
              <Card key={integration.id}>
                <CardHeader>
                  <div>
                    <CardTitle>{integration.name}</CardTitle>
                    <p className="mt-2 text-sm text-[var(--muted)]">{integration.description}</p>
                  </div>
                  <Badge tone={integration.health_status}>{integration.health_status}</Badge>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="rounded-2xl border px-4 py-3 text-sm">
                    Last synced: {integration.last_synced_at ? formatDate(integration.last_synced_at) : "Never"}
                  </div>
                  <div className="space-y-3">
                    {integration.runs.slice(0, 3).map((run) => (
                      <div key={run.id} className="rounded-2xl border px-4 py-3">
                        <div className="flex items-center justify-between gap-3">
                          <p className="font-semibold">{run.source_filename ?? "Manual import"}</p>
                          <Badge tone={run.status === "completed" ? "healthy" : run.status === "running" ? "medium" : "critical"}>
                            {run.status}
                          </Badge>
                        </div>
                        <p className="mt-2 text-sm text-[var(--muted)]">
                          {run.records_ingested} records • {formatDate(run.started_at)}
                        </p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
