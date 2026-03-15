type AnomalyScoreBadgeProps = {
  score: number;
  compact?: boolean;
};

function getScoreClasses(score: number) {
  if (score >= 0.8) {
    return "bg-red-100 text-red-700 ring-red-200";
  }

  if (score >= 0.65) {
    return "bg-brand-orange/10 text-brand-orange ring-brand-orange/20";
  }

  if (score >= 0.45) {
    return "bg-amber-100 text-amber-700 ring-amber-200";
  }

  return "bg-emerald-100 text-emerald-700 ring-emerald-200";
}

export function AnomalyScoreBadge({ score, compact = false }: AnomalyScoreBadgeProps) {
  return (
    <span
      className={`inline-flex rounded-full ring-1 ${compact ? "px-2.5 py-1 text-[11px]" : "px-3 py-1 text-xs"} font-semibold ${getScoreClasses(score)}`}
    >
      AI {Math.round(score * 100)}%
    </span>
  );
}
