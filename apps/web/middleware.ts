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

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  const token = request.cookies.get(AUTH_TOKEN_COOKIE)?.value;
  const role = request.cookies.get(AUTH_ROLE_COOKIE)?.value;
  const isProtected = protectedPaths.some((path) => pathname.startsWith(path));

  if (isProtected && !token) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  if (pathname.startsWith("/admin") && token && role !== "Admin") {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  if (pathname.startsWith("/login") && token) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
