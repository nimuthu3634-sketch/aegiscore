import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="soc-background flex min-h-screen items-center justify-center px-4">
      <div className="panel relative overflow-hidden rounded-[2.2rem] p-10 text-center shadow-premium">
        <div className="pointer-events-none absolute -right-10 top-0 h-32 w-32 rounded-full bg-brand-orange/10 blur-3xl" />
        <p className="text-xs uppercase tracking-[0.26em] text-brand-orange">404</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-brand-black">Page not found</h1>
        <p className="mt-3 max-w-md text-sm leading-7 text-brand-black/65">
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
