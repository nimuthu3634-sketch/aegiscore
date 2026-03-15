type StatCardProps = {
  label: string;
  value: string;
  change: string;
};

export function StatCard({ label, value, change }: StatCardProps) {
  return (
    <div className="rounded-[1.5rem] border border-brand-black/5 bg-white p-5 shadow-panel">
      <p className="text-sm text-brand-black/60">{label}</p>
      <div className="mt-4 flex items-end justify-between gap-4">
        <p className="text-3xl font-semibold text-brand-black">{value}</p>
        <span className="rounded-full bg-brand-orange/10 px-3 py-1 text-xs font-semibold text-brand-orange">
          {change}
        </span>
      </div>
    </div>
  );
}
