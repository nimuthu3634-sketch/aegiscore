export function formatDate(value?: string | null) {
  if (!value) {
    return "N/A";
  }
  return new Intl.DateTimeFormat("en", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function formatDateOnly(value?: string | null) {
  if (!value) {
    return "N/A";
  }
  return new Intl.DateTimeFormat("en", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(value));
}

export function formatNumber(value: number) {
  return new Intl.NumberFormat("en-US").format(value);
}

export function formatPercent(value?: number | null) {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return "N/A";
  }
  return `${(value * 100).toFixed(1)}%`;
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

export function truncate(value: string, maxLength = 140) {
  if (value.length <= maxLength) {
    return value;
  }
  if (maxLength <= 3) {
    return value.slice(0, maxLength);
  }
  return `${value.slice(0, maxLength - 3)}...`;
}

export function describeLatency(value?: number | null) {
  if (value === undefined || value === null) {
    return "Unavailable";
  }
  return `${value.toFixed(2)} ms`;
}
