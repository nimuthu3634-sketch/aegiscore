import { appConfig } from "@/lib/config";
import { clearAuthSession } from "@/lib/auth";

export class ApiError extends Error {
  status: number;
  payload?: unknown;

  constructor(message: string, status: number, payload?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

export function createQueryString(values: Record<string, string | number | boolean | null | undefined>) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(values)) {
    if (value === undefined || value === null || value === "") {
      continue;
    }
    params.set(key, String(value));
  }
  const rendered = params.toString();
  return rendered ? `?${rendered}` : "";
}

function extractApiErrorMessage(payload: unknown): string {
  if (typeof payload === "string" && payload.trim()) {
    return payload;
  }

  if (typeof payload !== "object" || !payload) {
    return "Request failed";
  }

  const candidate = payload as {
    detail?: unknown;
    message?: unknown;
    errors?: Array<{ msg?: string }>;
  };

  if (typeof candidate.detail === "string" && candidate.detail.trim()) {
    return candidate.detail;
  }

  if (typeof candidate.message === "string" && candidate.message.trim()) {
    return candidate.message;
  }

  if (candidate.detail && typeof candidate.detail === "object") {
    const nestedDetail = candidate.detail as {
      detail?: unknown;
      message?: unknown;
      app?: unknown;
      database?: unknown;
      redis?: unknown;
    };

    if (typeof nestedDetail.detail === "string" && nestedDetail.detail.trim()) {
      return nestedDetail.detail;
    }

    if (typeof nestedDetail.message === "string" && nestedDetail.message.trim()) {
      return nestedDetail.message;
    }

    if ("app" in nestedDetail || "database" in nestedDetail || "redis" in nestedDetail) {
      return "One or more platform services are currently unavailable.";
    }
  }

  if (Array.isArray(candidate.errors) && candidate.errors.length > 0) {
    const firstMessage = candidate.errors.find((error) => typeof error?.msg === "string")?.msg;
    if (firstMessage) {
      return firstMessage;
    }
  }

  return "Request failed";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  const bodyIsFormData = typeof FormData !== "undefined" && init?.body instanceof FormData;
  if (!bodyIsFormData) {
    headers.set("Content-Type", headers.get("Content-Type") ?? "application/json");
  }

  const response = await fetch(`${appConfig.apiBaseUrl}${path}`, {
    ...init,
    headers,
    cache: "no-store",
    credentials: "include",
  });

  const contentType = response.headers.get("content-type") ?? "";
  let payload: unknown;
  if (contentType.includes("application/json")) {
    payload = await response.json();
  } else {
    payload = await response.text();
  }

  if (response.status === 401) {
    clearAuthSession();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    throw new ApiError("Unauthorized", response.status, payload);
  }

  if (!response.ok) {
    const message = extractApiErrorMessage(payload);
    throw new ApiError(message, response.status, payload);
  }

  return payload as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: body ? JSON.stringify(body) : undefined }),
  upload: <T>(path: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<T>(path, { method: "POST", body: formData });
  },
};

export function downloadTextFile(filename: string, content: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
