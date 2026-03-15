import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "@/hooks/useAuth";

export function PublicOnlyRoute() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <div className="panel rounded-[2rem] px-8 py-10 text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brand-orange">
            AegisCore
          </p>
          <p className="mt-3 text-sm text-brand-black/65">Loading sign-in workspace...</p>
        </div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}
