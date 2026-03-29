import type { User } from "@/types/domain";
import { USER_STORAGE_KEY } from "@/lib/session";

export function setAuthSession(user: User) {
  localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
}

export function clearAuthSession() {
  localStorage.removeItem(USER_STORAGE_KEY);
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
