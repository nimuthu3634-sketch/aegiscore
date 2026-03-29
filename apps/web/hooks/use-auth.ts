"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { clearAuthSession, getStoredUser, setStoredUser } from "@/lib/auth";
import { appConfig } from "@/lib/config";
import type { User } from "@/types/domain";

export function useAuth() {
  return useQuery<User>({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      const user = await api.get<User>("/auth/me");
      setStoredUser(user);
      return user;
    },
    initialData: getStoredUser() ?? undefined,
    retry: false,
    staleTime: 60_000,
  });
}

export async function signOut() {
  try {
    await fetch(`${appConfig.apiBaseUrl}/auth/logout`, {
      method: "POST",
      credentials: "include",
    });
  } finally {
    clearAuthSession();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  }
}
