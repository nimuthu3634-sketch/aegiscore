import type { AuthResponse, AuthUser, LoginPayload, RegisterPayload } from "@/types/auth";

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

export { API_BASE_URL };
