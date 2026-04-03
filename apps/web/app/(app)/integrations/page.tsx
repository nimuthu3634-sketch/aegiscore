"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronDown, ChevronUp, RefreshCw, Settings, ShieldCheck } from "lucide-react";
import { useState } from "react";
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
import { canManageOperations, isAdmin } from "@/lib/permissions";
import { maxUploadBytes, validateImportFile } from "@/lib/validation";
import { useAuth } from "@/hooks/use-auth";
import type { ImportResult, Integration, PageResult } from "@/types/domain";

// ─── schemas ────────────────────────────────────────────────────────────────

type ImportValues = { integration: string; file?: File };

const importSchema = z
  .object({
    integration: z.string().min(1, "Select an integration."),
    file: z.instanceof(File, { message: "Choose a file to import." }).optional(),
  })
  .refine((v) => v.file instanceof File, { path: ["file"], message: "Choose a file to import." });

const configSchema = z.object({
  endpoint_url: z.string().url("Enter a valid http/https URL.").or(z.literal("")),
  auth_type: z.enum(["none", "bearer", "basic"]),
  username: z.string().max(200).optional(),
  password: z.string().max(500).optional(),
  api_token: z.string().max(500).optional(),
  verify_tls: z.boolean(),
  timeout_seconds: z.coerce.number().int().min(5).max(120),
  lookback_minutes: z.coerce.number().int().min(1).max(10080),
});
type ConfigValues = z.infer<typeof configSchema>;

// ─── helpers ─────────────────────────────────────────────────────────────────

function IntegrationConfigForm({
  integration,
  onClose,
}: {
  integration: Integration;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const cfg = integration.configuration;

  const form = useForm<ConfigValues>({
    resolver: zodResolver(configSchema),
    defaultValues: {
      endpoint_url: cfg?.endpoint_url ?? "",
      auth_type: (cfg?.auth_type ?? "none") as "none" | "bearer" | "basic",
      username: cfg?.username ?? "",
      password: "",
      api_token: "",
      verify_tls: cfg?.verify_tls ?? true,
      timeout_seconds: cfg?.timeout_seconds ?? 15,
      lookback_minutes: cfg?.lookback_minutes ?? 60,
    },
  });

  const authType = form.watch("auth_type");

  const saveMutation = useMutation({
    mutationFn: (values: ConfigValues) => {
      const payload: Record<string, unknown> = {
        endpoint_url: values.endpoint_url || null,
        auth_type: values.auth_type,
        verify_tls: values.verify_tls,
        timeout_seconds: values.timeout_seconds,
        lookback_minutes: values.lookback_minutes,
      };
      if (values.auth_type === "basic") {
        if (values.username) payload.username = values.username;
        if (values.password) payload.password = values.password;
      }
      if (values.auth_type === "bearer" && values.api_token) {
        payload.api_token = values.api_token;
      }
      return api.patch<Integration>(`/integrations/${integration.slug}`, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["integrations"] });
      onClose();
    },
  });

  return (
    <form
      className="space-y-4 border-t pt-4"
      onSubmit={form.handleSubmit((values) => saveMutation.mutate(values))}
    >
      <p className="text-sm font-semibold text-[#111111]">Endpoint configuration</p>

      <FormField label="Endpoint URL" error={form.formState.errors.endpoint_url?.message}>
        <input
          {...form.register("endpoint_url")}
          type="url"
          placeholder="https://wazuh-server:55000/alerts"
          className="block w-full rounded-xl border bg-white px-3 py-2.5 text-sm"
        />
      </FormField>

      <div className="grid gap-4 sm:grid-cols-2">
        <FormField label="Auth type" error={form.formState.errors.auth_type?.message}>
          <Select {...form.register("auth_type")}>
            <option value="none">None</option>
            <option value="bearer">Bearer token</option>
            <option value="basic">Basic auth</option>
          </Select>
        </FormField>

        <FormField label="TLS verification">
          <label className="flex items-center gap-2 pt-2 text-sm">
            <input type="checkbox" {...form.register("verify_tls")} className="rounded border" />
            Verify TLS certificate
          </label>
        </FormField>
      </div>

      {authType === "basic" && (
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField label="Username" error={form.formState.errors.username?.message}>
            <input {...form.register("username")} className="block w-full rounded-xl border bg-white px-3 py-2.5 text-sm" />
          </FormField>
          <FormField label="Password (leave blank to keep existing)" error={form.formState.errors.password?.message}>
            <input {...form.register("password")} type="password" autoComplete="new-password" className="block w-full rounded-xl border bg-white px-3 py-2.5 text-sm" />
          </FormField>
        </div>
      )}

      {authType === "bearer" && (
        <FormField label="API token (leave blank to keep existing)" error={form.formState.errors.api_token?.message}>
          <input {...form.register("api_token")} type="password" autoComplete="new-password" className="block w-full rounded-xl border bg-white px-3 py-2.5 text-sm" />
        </FormField>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <FormField label="Timeout (seconds)" error={form.formState.errors.timeout_seconds?.message}>
          <input {...form.register("timeout_seconds")} type="number" min={5} max={120} className="block w-full rounded-xl border bg-white px-3 py-2.5 text-sm" />
        </FormField>
        <FormField label="Lookback window (minutes)" error={form.formState.errors.lookback_minutes?.message}>
          <input {...form.register("lookback_minutes")} type="number" min={1} max={10080} className="block w-full rounded-xl border bg-white px-3 py-2.5 text-sm" />
        </FormField>
      </div>

      {saveMutation.isError && (
        <p className="text-sm text-red-600">
          {saveMutation.error instanceof Error ? saveMutation.error.message : "Save failed."}
        </p>
      )}

      <div className="flex gap-3">
        <Button type="submit" disabled={saveMutation.isPending}>
          {saveMutation.isPending ? "Saving..." : "Save configuration"}
        </Button>
        <Button type="button" variant="outline" onClick={onClose}>
          Cancel
        </Button>
      </div>
    </form>
  );
}

function IntegrationCard({
  integration,
  canConfigure,
  canSync,
}: {
  integration: Integration;
  canConfigure: boolean;
  canSync: boolean;
}) {
  const queryClient = useQueryClient();
  const [showConfig, setShowConfig] = useState(false);

  const syncMutation = useMutation({
    mutationFn: () => api.post<ImportResult>(`/integrations/${integration.slug}/sync`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["integrations"] });
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
      queryClient.invalidateQueries({ queryKey: ["logs"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] });
    },
  });

  const testMutation = useMutation({
    mutationFn: () =>
      api.post<{ reachable: boolean | null; status: string; detail: string; http_status: number | null; latency_ms: number | null }>(
        `/integrations/${integration.slug}/test`,
      ),
  });

  const isSyncCapable = integration.supports_manual_sync ?? false;
  const isLabOnly = integration.lab_only_import ?? false;
  const isConfigured = integration.configuration?.configured ?? false;

  return (
    <Card>
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
            <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Type</p>
            <p className="mt-3 font-semibold">{integration.type}</p>
          </div>
          <div className="rounded-[1.25rem] border bg-white p-4">
            <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Last sync</p>
            <p className="mt-3 font-semibold">{formatDate(integration.last_synced_at)}</p>
          </div>
          <div className="rounded-[1.25rem] border bg-white p-4">
            <p className="text-xs uppercase tracking-[0.24em] text-[#8f8f8f]">Enabled</p>
            <p className="mt-3 font-semibold">{integration.enabled ? "Yes" : "No"}</p>
          </div>
        </div>

        {/* Status / last error */}
        {integration.last_error && (
          <div className="rounded-[1.25rem] border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            {integration.last_error}
          </div>
        )}

        {/* Sync now + test + configure buttons (sync-capable only) */}
        {isSyncCapable && !isLabOnly && (
          <div className="flex flex-wrap items-center gap-3">
            {canSync && (
              <Button
                size="sm"
                disabled={syncMutation.isPending || !isConfigured}
                onClick={() => syncMutation.mutate()}
                title={!isConfigured ? "Configure an endpoint URL first" : undefined}
              >
                <RefreshCw className={`mr-2 h-4 w-4 ${syncMutation.isPending ? "animate-spin" : ""}`} />
                {syncMutation.isPending ? "Syncing..." : "Sync now"}
              </Button>
            )}

            {canSync && (
              <Button
                size="sm"
                variant="outline"
                disabled={testMutation.isPending || !isConfigured}
                onClick={() => testMutation.mutate()}
                title={!isConfigured ? "Configure an endpoint URL first" : "Test connectivity without ingesting data"}
              >
                <ShieldCheck className={`mr-2 h-4 w-4 ${testMutation.isPending ? "animate-pulse" : ""}`} />
                {testMutation.isPending ? "Testing..." : "Test connection"}
              </Button>
            )}

            {canConfigure && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => setShowConfig((previous) => !previous)}
              >
                <Settings className="mr-2 h-4 w-4" />
                {showConfig ? "Hide config" : "Configure"}
                {showConfig ? <ChevronUp className="ml-2 h-4 w-4" /> : <ChevronDown className="ml-2 h-4 w-4" />}
              </Button>
            )}

            {syncMutation.isError && (
              <span className="text-sm text-red-600">
                {syncMutation.error instanceof Error ? syncMutation.error.message : "Sync failed."}
              </span>
            )}
            {syncMutation.data && (
              <span className="text-sm text-green-700">
                Sync complete — {syncMutation.data.alerts_created} alerts, {syncMutation.data.logs_created} logs ingested.
              </span>
            )}
            {testMutation.data && (
              <span className={`text-sm font-medium ${testMutation.data.reachable ? "text-green-700" : "text-red-600"}`}>
                {testMutation.data.reachable ? `Reachable` : `Unreachable`}
                {testMutation.data.http_status ? ` · HTTP ${testMutation.data.http_status}` : ""}
                {testMutation.data.latency_ms != null ? ` · ${testMutation.data.latency_ms}ms` : ""}
                {testMutation.data.detail ? ` — ${testMutation.data.detail}` : ""}
              </span>
            )}
            {testMutation.isError && (
              <span className="text-sm text-red-600">
                {testMutation.error instanceof Error ? testMutation.error.message : "Connection test failed."}
              </span>
            )}
          </div>
        )}

        {/* Collapsible config form */}
        {showConfig && isSyncCapable && canConfigure && (
          <IntegrationConfigForm
            integration={integration}
            onClose={() => setShowConfig(false)}
          />
        )}

        {/* Recent run history */}
        <div className="space-y-3">
          <p className="text-sm font-semibold text-[#111111]">Recent sync history</p>
          {integration.runs.length ? (
            integration.runs.slice(0, 4).map((run) => (
              <div key={run.id} className="rounded-[1.25rem] border bg-white p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-semibold text-[#111111]">{run.source_filename ?? "Manual sync"}</p>
                    <p className="mt-1 text-sm text-[#6f6f6f]">
                      {run.records_ingested} records &middot; started {formatDate(run.started_at)}
                    </p>
                  </div>
                  <Badge tone={run.status === "completed" ? "healthy" : run.status === "running" ? "medium" : "critical"}>
                    {run.status}
                  </Badge>
                </div>
                {run.error_message && (
                  <p className="mt-2 text-xs text-red-600">{run.error_message}</p>
                )}
              </div>
            ))
          ) : (
            <p className="text-sm text-[#6f6f6f]">No sync history recorded yet.</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ─── page ────────────────────────────────────────────────────────────────────

export default function IntegrationsPage() {
  const queryClient = useQueryClient();
  const { data: currentUser } = useAuth();
  const canImport = canManageOperations(currentUser?.role);
  const canConfigure = isAdmin(currentUser?.role);

  const form = useForm<ImportValues>({
    resolver: zodResolver(importSchema),
    defaultValues: { integration: "wazuh", file: undefined },
  });

  const selectedIntegration = form.watch("integration");

  const query = useQuery({
    queryKey: ["integrations", "list"],
    queryFn: () =>
      api.get<PageResult<Integration>>(
        `/integrations${createQueryString({ page: 1, page_size: 12 })}`
      ),
  });

  const importMutation = useMutation({
    mutationFn: async (values: ImportValues) => {
      if (!values.file) throw new Error("Choose a file to import.");
      const selectedConfig = query.data?.items.find((i) => i.slug === values.integration);
      validateImportFile(values.file, selectedConfig);
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

  if (query.isLoading) return <LoadingState lines={7} />;
  if (query.isError || !query.data)
    return (
      <ErrorState
        description={query.error instanceof Error ? query.error.message : "Integrations could not be loaded."}
        onRetry={() => query.refetch()}
      />
    );

  const selectedIntegrationConfig = query.data.items.find((i) => i.slug === selectedIntegration);
  const acceptedFormats = selectedIntegrationConfig?.supported_formats ?? ["json"];
  const acceptValue = acceptedFormats.map((f) => `.${f}`).join(",");

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Telemetry sources"
        title="Integrations"
        description="Monitor connector health, configure live Wazuh and Suricata endpoints, trigger manual syncs, and safely import lab-only telemetry files."
        actions={<Badge tone="medium">Defensive telemetry only</Badge>}
      />

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        {/* ── Import form ────────────────────────────────────────────── */}
        <Card>
          <CardHeader>
            <CardTitle>Import telemetry file</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-[1.25rem] border bg-[#fff7f1] p-4 text-sm leading-6 text-[#8a4e16]">
              Wazuh and Suricata are defensive telemetry sources. Nmap and Hydra are supported only as
              lab-safe imported result files — they are never executed by AegisCore.
            </div>

            {canImport ? (
              <form
                className="space-y-4"
                onSubmit={form.handleSubmit((values) => importMutation.mutate(values))}
              >
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
                    title="Choose a telemetry file to import"
                    accept={acceptValue}
                    onChange={(e) =>
                      form.setValue("file", e.target.files?.[0] ?? undefined, {
                        shouldValidate: true,
                      })
                    }
                  />
                </FormField>

                <p className="text-xs leading-5 text-[#7a7a7a]">
                  Accepted formats: {acceptedFormats.map((f) => `.${f}`).join(", ")}. Maximum size:{" "}
                  {maxUploadBytes / (1024 * 1024)} MB.
                </p>

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
                      Your role can review connector health, but only Admins and Analysts can import lab
                      files.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {importMutation.data ? (
              <div className="rounded-[1.25rem] border bg-[#fcfcfc] p-4 text-sm">
                <p className="font-semibold text-[#111111]">Import complete</p>
                <p className="mt-2 text-[#5f5f5f]">
                  {importMutation.data.alerts_created} alerts, {importMutation.data.logs_created} logs,
                  and {importMutation.data.assets_touched} assets updated.
                </p>
              </div>
            ) : null}

            {importMutation.error instanceof Error ? (
              <div className="rounded-[1.25rem] border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                {importMutation.error.message}
              </div>
            ) : null}
          </CardContent>
        </Card>

        {/* ── Integration cards ───────────────────────────────────────── */}
        <div className="grid gap-6">
          {query.data.items.length ? (
            query.data.items.map((integration) => (
              <IntegrationCard
                key={integration.id}
                integration={integration}
                canConfigure={canConfigure}
                canSync={canImport}
              />
            ))
          ) : (
            <EmptyState
              title="No integrations found"
              description="Connector health cards will appear here once telemetry sources have been initialised in the backend."
            />
          )}
        </div>
      </div>
    </div>
  );
}
