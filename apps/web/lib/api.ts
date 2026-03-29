import { appConfig } from "@/lib/config";
import { clearAuthSession, getToken } from "@/lib/auth";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Content-Type", headers.get("Content-Type") ?? "application/json");
  const token = typeof window !== "undefined" ? getToken() : "";
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${appConfig.apiBaseUrl}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  if (response.status === 401) {
    clearAuthSession();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "Request failed");
  }

  if (response.headers.get("content-type")?.includes("text/csv") || response.headers.get("content-type")?.includes("text/plain")) {
    return (await response.text()) as T;
  }

  return (await response.json()) as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: body ? JSON.stringify(body) : undefined }),
  upload: async <T>(path: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    const token = getToken();
    const response = await fetch(`${appConfig.apiBaseUrl}${path}`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      body: formData,
    });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    return (await response.json()) as T;
  },
};
