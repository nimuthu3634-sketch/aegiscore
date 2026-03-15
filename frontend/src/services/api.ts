import type { AuthResponse, AuthUser, LoginPayload, RegisterPayload } from "@/types/auth";
import type {
  AlertApiRecord,
  AlertFilters,
  AlertListResponse,
  AlertStatusUpdatePayload,
  DashboardChartsResponse,
  DashboardRecentAlert,
  DashboardRecentIncident,
  DashboardSummaryResponse,
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

export { API_BASE_URL };
