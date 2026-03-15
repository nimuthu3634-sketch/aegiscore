import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-brand-light px-4">
      <div className="rounded-[2rem] bg-white p-10 text-center shadow-panel">
        <p className="text-xs uppercase tracking-[0.24em] text-brand-orange">404</p>
        <h1 className="mt-3 text-3xl font-semibold text-brand-black">Page not found</h1>
        <p className="mt-3 max-w-md text-sm leading-6 text-brand-black/65">
          The route does not exist in this scaffold yet. Return to the dashboard shell to continue
          building the project.
        </p>
        <Link to="/dashboard" className="btn-primary mt-6">
          Back to dashboard
        </Link>
      </div>
    </div>
  );
}
