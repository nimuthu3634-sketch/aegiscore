import type { AuthResponse, AuthUser, LoginPayload, RegisterPayload } from "@/types/auth";
import type {
  AlertApiRecord,
  AlertFilters,
  AlertListResponse,
  AlertStatusUpdatePayload,
  DashboardAnomalySummaryResponse,
  DashboardChartsResponse,
  DashboardRecentAlert,
  DashboardRecentIncident,
  DashboardSummaryResponse,
  IncidentCreatePayload,
  IncidentFilters,
  IncidentListResponse,
  IncidentApiRecord,
  IncidentUpdatePayload,
  HydraImportPayload,
  HydraImportResponse,
  HydraIntegrationStatus,
  IntegrationApiRecord,
  LogEntryRecord,
  LogIngestPayload,
  LogListResponse,
  NmapImportPayload,
  NmapImportResponse,
  NmapIntegrationStatus,
  ReportApiRecord,
  ReportFilters,
  ReportGeneratePayload,
  ReportsSummaryResponse,
  SuricataImportPayload,
  SuricataImportResponse,
  SuricataIntegrationStatus,
  VirtualMachineCreatePayload,
  VirtualMachineRecord,
  VirtualMachineUpdatePayload,
  WazuhImportPayload,
  WazuhImportResponse,
  WazuhIntegrationStatus,
} from "@/types/domain";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let errorMessage = "The request could not be completed.";

    try {
      const errorBody = (await response.json()) as { detail?: string };
      if (errorBody.detail) {
        errorMessage = errorBody.detail;
      }
    } catch {
      errorMessage = response.statusText || errorMessage;
    }

    throw new Error(errorMessage);
  }

  return (await response.json()) as T;
}

export async function fetchHealth() {
  return request("/health", { method: "GET" });
}

export async function loginRequest(payload: LoginPayload) {
  return request<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function registerRequest(payload: RegisterPayload) {
  return request<AuthResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchCurrentUser(token: string) {
  return request<AuthUser>("/auth/me", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function fetchDashboardSummary(token: string) {
  return request<DashboardSummaryResponse>("/dashboard/summary", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function fetchDashboardCharts(token: string) {
  return request<DashboardChartsResponse>("/dashboard/charts", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function fetchDashboardRecentAlerts(token: string) {
  return request<DashboardRecentAlert[]>("/dashboard/recent-alerts", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function fetchDashboardRecentIncidents(token: string) {
  return request<DashboardRecentIncident[]>("/dashboard/recent-incidents", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function fetchDashboardAnomalySummary(token: string) {
  return request<DashboardAnomalySummaryResponse>("/dashboard/anomaly-summary", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function fetchAlerts(token: string, filters: AlertFilters = {}) {
  const queryParams = new URLSearchParams();

  if (filters.search) {
    queryParams.set("search", filters.search);
  }

  if (filters.severity) {
    queryParams.set("severity", filters.severity);
  }

  if (filters.status) {
    queryParams.set("status", filters.status);
  }

  if (filters.source_tool) {
    queryParams.set("source_tool", filters.source_tool);
  }

  queryParams.set("page", String(filters.page ?? 1));
  queryParams.set("page_size", String(filters.page_size ?? 8));

  return request<AlertListResponse>(`/alerts?${queryParams.toString()}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function fetchAlertById(token: string, alertId: string) {
  return request<AlertApiRecord>(`/alerts/${alertId}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function patchAlertStatus(
  token: string,
  alertId: string,
  payload: AlertStatusUpdatePayload,
) {
  return request<AlertApiRecord>(`/alerts/${alertId}/status`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
}

export async function fetchIncidents(token: string, filters: IncidentFilters = {}) {
  const queryParams = new URLSearchParams();

  if (filters.priority) {
    queryParams.set("priority", filters.priority);
  }

  if (filters.status) {
    queryParams.set("status", filters.status);
  }

  if (filters.assignee_id) {
    queryParams.set("assignee_id", filters.assignee_id);
  }

  const queryString = queryParams.toString();

  return request<IncidentListResponse>(`/incidents${queryString ? `?${queryString}` : ""}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function fetchIncidentById(token: string, incidentId: string) {
  return request<IncidentApiRecord>(`/incidents/${incidentId}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function createIncident(token: string, payload: IncidentCreatePayload) {
  return request<IncidentApiRecord>("/incidents", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
}

export async function patchIncident(
  token: string,
  incidentId: string,
  payload: IncidentUpdatePayload,
) {
  return request<IncidentApiRecord>(`/incidents/${incidentId}`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
}

export async function fetchLogs(token: string) {
  return request<LogListResponse>("/logs", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function fetchLogById(token: string, logId: string) {
  return request<LogEntryRecord>(`/logs/${logId}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function ingestLog(token: string, payload: LogIngestPayload) {
  return request<LogEntryRecord>("/logs/ingest", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
}

export async function fetchReports(token: string, filters: ReportFilters = {}) {
  const queryParams = new URLSearchParams();

  if (filters.date_from) {
    queryParams.set("date_from", filters.date_from);
  }

  if (filters.date_to) {
    queryParams.set("date_to", filters.date_to);
  }

  const queryString = queryParams.toString();

  return request<ReportApiRecord[]>(`/reports${queryString ? `?${queryString}` : ""}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function fetchReportsSummary(token: string, filters: ReportFilters = {}) {
  const queryParams = new URLSearchParams();

  if (filters.date_from) {
    queryParams.set("date_from", filters.date_from);
  }

  if (filters.date_to) {
    queryParams.set("date_to", filters.date_to);
  }

  const queryString = queryParams.toString();

  return request<ReportsSummaryResponse>(`/reports/summary${queryString ? `?${queryString}` : ""}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function generateReport(token: string, payload: ReportGeneratePayload) {
  return request<ReportApiRecord>("/reports/generate", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
}

export async function fetchIntegrationStatuses(token: string) {
  return request<IntegrationApiRecord[]>("/integrations/status", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function fetchWazuhIntegrationStatus(token: string) {
  return request<WazuhIntegrationStatus>("/integrations/wazuh/status", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function importWazuhAlerts(token: string, payload: WazuhImportPayload) {
  return request<WazuhImportResponse>("/integrations/wazuh/import", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
}

export async function fetchSuricataIntegrationStatus(token: string) {
  return request<SuricataIntegrationStatus>("/integrations/suricata/status", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function importSuricataEvents(token: string, payload: SuricataImportPayload) {
  return request<SuricataImportResponse>("/integrations/suricata/import", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
}

export async function fetchNmapIntegrationStatus(token: string) {
  return request<NmapIntegrationStatus>("/integrations/nmap/status", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function importNmapResults(token: string, payload: NmapImportPayload) {
  return request<NmapImportResponse>("/integrations/nmap/import", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
}

export async function fetchHydraIntegrationStatus(token: string) {
  return request<HydraIntegrationStatus>("/integrations/hydra/status", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function importHydraResults(token: string, payload: HydraImportPayload) {
  return request<HydraImportResponse>("/integrations/hydra/import", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
}

export async function fetchVirtualLabMachines(token: string) {
  return request<VirtualMachineRecord[]>("/integrations/virtualbox/lab", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function createVirtualLabMachine(token: string, payload: VirtualMachineCreatePayload) {
  return request<VirtualMachineRecord>("/integrations/virtualbox/lab", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
}

export async function patchVirtualLabMachine(
  token: string,
  vmId: string,
  payload: VirtualMachineUpdatePayload,
) {
  return request<VirtualMachineRecord>(`/integrations/virtualbox/lab/${vmId}`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
}

export { API_BASE_URL };
