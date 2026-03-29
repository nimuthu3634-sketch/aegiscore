import type { Role } from "@/types/domain";

export function isAdmin(role?: Role | null) {
  return role === "Admin";
}

export function canManageOperations(role?: Role | null) {
  return role === "Admin" || role === "Analyst";
}
