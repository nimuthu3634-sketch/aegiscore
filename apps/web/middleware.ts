import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { AUTH_ROLE_COOKIE, AUTH_TOKEN_COOKIE } from "@/lib/session";

const protectedPaths = [
  "/dashboard",
  "/alerts",
  "/incidents",
  "/logs",
  "/assets",
  "/integrations",
  "/ai",
  "/analytics",
  "/reports",
  "/settings",
  "/admin",
  "/profile",
];

type SessionPayload = {
  exp?: number;
  role?: string;
};

function decodeTokenPayload(token: string): SessionPayload | null {
  const parts = token.split(".");
  if (parts.length !== 3 || !parts[1]) {
    return null;
  }

  try {
    const normalized = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
    return JSON.parse(atob(padded)) as SessionPayload;
  } catch {
    return null;
  }
}

function clearAuthCookies(response: NextResponse) {
  response.cookies.set(AUTH_TOKEN_COOKIE, "", { expires: new Date(0), path: "/" });
  response.cookies.set(AUTH_ROLE_COOKIE, "", { expires: new Date(0), path: "/" });
}

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  const token = request.cookies.get(AUTH_TOKEN_COOKIE)?.value;
  const isProtected = protectedPaths.some((path) => pathname.startsWith(path));
  const payload = token ? decodeTokenPayload(token) : null;
  const isExpired = typeof payload?.exp === "number" && payload.exp * 1000 <= Date.now();
  const hasValidSession = Boolean(token && payload && !isExpired);
  const shouldClearCookies = Boolean(token && (!payload || isExpired));
  const role = typeof payload?.role === "string" ? payload.role : request.cookies.get(AUTH_ROLE_COOKIE)?.value;

  if (isProtected && !hasValidSession) {
    const response = NextResponse.redirect(new URL("/login", request.url));
    if (shouldClearCookies) {
      clearAuthCookies(response);
    }
    return response;
  }

  if (pathname.startsWith("/admin") && hasValidSession && role !== "Admin") {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  if (pathname.startsWith("/login") && hasValidSession) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  const response = NextResponse.next();
  if (shouldClearCookies) {
    clearAuthCookies(response);
  }
  return response;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
