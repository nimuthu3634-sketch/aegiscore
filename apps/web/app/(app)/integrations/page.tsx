"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ShieldCheck } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { EmptyState } from "@/components/feedback/empty-state";
import { ErrorState } from "@/components/feedback/error-state";
import { LoadingState } from "@/components/feedback/loading-state";
import { FormField } from "@/components/forms/form-field";
import { PageHeader } from "@/components/shared/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { api, createQueryString } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { canManageOperations } from "@/lib/permissions";
import { useAuth } from "@/hooks/use-auth";
import type { ImportResult, Integration, PageResult } from "@/types/domain";

type ImportValues = {
  integration: string;
  file?: File;
};

const importSchema = z
  .object({
    integration: z.string().min(1, "Select an integration."),
    file: z.instanceof(File, { message: "Choose a file to import." }).optional(),
  })
  .refine((values) => values.file instanceof File, {
    path: ["file"],
    message: "Choose a file to import.",
  });

export default function IntegrationsPage() {
  const queryClient = useQueryClient();
  const { data: currentUser } = useAuth();
  const canImport = canManageOperations(currentUser?.role);

  const form = useForm<ImportValues>({
    resolver: zodResolver(importSchema),
    defaultValues: { integration: "wazuh", file: undefined },
  });

  const selectedIntegration = form.watch("integration");

  const query = useQuery({
    queryKey: ["integrations", "list"],
    queryFn: () => api.get<PageResult<Integration>>(`/integrations${createQueryString({ page: 1, page_size: 12 })}`),
  });

  const importMutation = useMutation({
    mutationFn: async (values: ImportValues) => {
      if (!values.file) {
        throw new Error("Choose a file to import.");
      }
      return api.upload<ImportResult>(`/integrations/${values.integration}/import`, values.file);
    },
    onSuccess: () => {
      form.reset({ integration: selectedIntegration, file: undefined });
      queryClient.invalidateQueries({ queryKey: ["integrations"] });
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
      queryClient.invalidateQueries({ queryKey: ["logs"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] });
    },
  });

  if (query.isLoading) {
    return <LoadingState lines={7} />;
  }

  if (query.isError || !query.data) {
    return <ErrorState description={query.error instanceof Error ? query.error.message : "Integrations could not be loaded."} onRetry={() => query.refetch()} />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Telemetry sources"
        title="Integrations"
        description="Monitor connector health, review sync history, and safely import lab-only telemetry files without exposing any scanning or offensive execution workflow."
        actions={<Badge tone="medium">Defensive telemetry only</Badge>}
      />

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Import telemetry file</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-[1.25rem] border bg-[#fff7f1] p-4 text-sm leading-6 text-[#8a4e16]">
              Wazuh and Suricata are treated as defensive telemetry sources. Nmap and Hydra are supported only as lab-safe imported result files and are never executed from the application.
            </div>

            {canImport ? (
              <form className="space-y-4" onSubmit={form.handleSubmit((values) => importMutation.mutate(values))}>
                <FormField label="Integration" error={form.formState.errors.integration?.message}>
                  <Select {...form.register("integration")}>
                    <option value="wazuh">Wazuh</option>
                    <option value="suricata">Suricata</option>
                    <option value="nmap">Nmap import</option>
                    <option value="hydra">Hydra import</option>
                  </Select>
                </FormField>

                <FormField label="File" error={form.formState.errors.file?.message}>
                  <input
                    className="block w-full rounded-xl border bg-white px-3 py-3 text-sm"
                    type="file"
                    accept=".json,.log,.ndjson,.txt,.xml"
                    onChange={(event) => form.setValue("file", event.target.files?.[0] ?? undefined, { shouldValidate: true })}
                  />
                </FormField>

                <Button type="submit" disabled={importMutation.isPending}>
                  {importMutation.isPending ? "Importing telemetry..." : "Import file"}
                </Button>
              </form>
            ) : (
              <div className="rounded-[1.25rem] border bg-white p-5">
                <div className="flex items-center gap-3">
                  <div className="rounded-full bg-[#fff4eb] p-3 text-[#FF7A1A]">
                    <ShieldCheck className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="font-semibold text-[#111111]">Read-only integration access</p>
                    <p className="mt-1 text-sm text-[#6f6f6f]">
                      Your current role can review connector health and sync history, but only admins and analysts can import lab files.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {importMutation.data ? (
              <div className="rounded-[1.25rem] border bg-[#fcfcfc] p-4 text-sm">
                <p className="font-semibold text-[#111111]">Import complete</p>
                <p className="mt-2 text-[#5f5f5f]">
                  {importMutation.data.alerts_created} alerts, {importMutation.data.logs_created} logs, and {importMutation.data.assets_touched} assets updated.
                </p>
              </div>
            ) : null}
          </CardContent>
        </Card>

        <div className="grid gap-6">
          {query.data.items.length ? (
            query.data.items.map((integration) => (
              <Card key={integration.id}>
                <CardHeader>
                  <div>
                    <CardTitle>{integration.name}</CardTitle>
                    <p className="mt-2 text-sm leading-6 text-[#6f6f6f]">{integration.description}</p>
                  </div>
                  <Badge tone={integration.health_status}>{integration.health_status}</Badge>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-3 sm:grid-cols-3">
                    <div className="rounded-[1.25rem] border bg-white p-4">
                      <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Connector type</p>
                      <p className="mt-3 font-semibold">{integration.type}</p>
                    </div>
                    <div className="rounded-[1.25rem] border bg-white p-4">
                      <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Enabled</p>
                      <p className="mt-3 font-semibold">{integration.enabled ? "Yes" : "No"}</p>
                    </div>
                    <div className="rounded-[1.25rem] border bg-white p-4">
                      <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Last sync</p>
                      <p className="mt-3 font-semibold">{formatDate(integration.last_synced_at)}</p>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <p className="text-sm font-semibold text-[#111111]">Recent sync history</p>
                    {integration.runs.length ? (
                      integration.runs.slice(0, 4).map((run) => (
                        <div key={run.id} className="rounded-[1.25rem] border bg-white p-4">
                          <div className="flex items-center justify-between gap-3">
                            <div>
                              <p className="font-semibold text-[#111111]">{run.source_filename ?? "Manual import"}</p>
                              <p className="mt-1 text-sm text-[#6f6f6f]">
                                {run.records_ingested} records | started {formatDate(run.started_at)}
                              </p>
                            </div>
                            <Badge tone={run.status === "completed" ? "healthy" : run.status === "running" ? "medium" : "critical"}>{run.status}</Badge>
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-[#6f6f6f]">No sync history recorded yet.</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))
          ) : (
            <EmptyState
              title="No integrations found"
              description="Connector health cards will appear here once telemetry sources have been initialized in the backend."
            />
          )}
        </div>
      </div>
    </div>
  );
}
