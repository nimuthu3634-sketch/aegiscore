import type { User } from "@/types/domain";

const TOKEN_COOKIE = "auth_token";
const USER_STORAGE_KEY = "aegiscore_user";

export function setAuthSession(token: string, user: User) {
  document.cookie = `${TOKEN_COOKIE}=${token}; path=/; max-age=86400; SameSite=Lax`;
  localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
}

export function clearAuthSession() {
  document.cookie = `${TOKEN_COOKIE}=; path=/; max-age=0; SameSite=Lax`;
  localStorage.removeItem(USER_STORAGE_KEY);
}

export function getToken() {
  if (typeof document === "undefined") {
    return "";
  }
  const cookie = document.cookie
    .split("; ")
    .find((entry) => entry.startsWith(`${TOKEN_COOKIE}=`));
  return cookie?.split("=")[1] ?? "";
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") {
    return null;
  }
  const raw = localStorage.getItem(USER_STORAGE_KEY);
  return raw ? (JSON.parse(raw) as User) : null;
}

export function setStoredUser(user: User) {
  if (typeof window === "undefined") {
    return;
  }
  localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
}
