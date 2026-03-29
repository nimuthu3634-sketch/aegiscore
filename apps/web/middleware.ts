import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

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
  const token = request.cookies.get("auth_token")?.value;
  const isProtected = protectedPaths.some((path) => request.nextUrl.pathname.startsWith(path));

  if (isProtected && !token) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  if (request.nextUrl.pathname.startsWith("/login") && token) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
