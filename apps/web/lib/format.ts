export function formatDate(value?: string | null) {
  if (!value) {
    return "N/A";
  }
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function toTitleCase(value: string) {
  return value.replace(/[_-]/g, " ").replace(/\b\w/g, (match) => match.toUpperCase());
}

export function scoreTone(score: number) {
  if (score >= 85) return "critical";
  if (score >= 65) return "high";
  if (score >= 35) return "medium";
  return "low";
}
