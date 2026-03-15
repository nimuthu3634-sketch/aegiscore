export const dashboardMetrics = [
  { label: "Active alerts", value: "128", change: "+14 today" },
  { label: "Open incidents", value: "12", change: "2 escalated" },
  { label: "Log events", value: "48.3K", change: "Wazuh + Suricata" },
  { label: "Anomaly score", value: "0.72", change: "Model online" }
];

export const alertTrendData = [
  { name: "Mon", alerts: 18 },
  { name: "Tue", alerts: 24 },
  { name: "Wed", alerts: 31 },
  { name: "Thu", alerts: 22 },
  { name: "Fri", alerts: 28 },
  { name: "Sat", alerts: 19 },
  { name: "Sun", alerts: 26 }
];

export const sourceCoverageData = [
  { name: "Wazuh", value: 56 },
  { name: "Suricata", value: 29 },
  { name: "Nmap", value: 9 },
  { name: "Hydra", value: 6 }
];

export const recentActivity = [
  {
    title: "Suspicious login burst detected",
    meta: "Hydra lab simulation imported · 4 minutes ago"
  },
  {
    title: "Suricata traffic anomaly flagged",
    meta: "HTTP inspection rule matched · 12 minutes ago"
  },
  {
    title: "Wazuh endpoint policy update completed",
    meta: "3 agents refreshed · 27 minutes ago"
  }
];

export const alertRows = [
  {
    id: "ALT-1001",
    title: "Multiple failed SSH logins",
    severity: "high",
    status: "new",
    source: "Wazuh",
    time: "2026-03-15 10:24"
  },
  {
    id: "ALT-1002",
    title: "Suricata detected uncommon DNS query",
    severity: "medium",
    status: "triaged",
    source: "Suricata",
    time: "2026-03-15 10:07"
  },
  {
    id: "ALT-1003",
    title: "Hydra lab result imported",
    severity: "low",
    status: "resolved",
    source: "Hydra",
    time: "2026-03-15 09:48"
  },
  {
    id: "ALT-1004",
    title: "Open port exposure from scheduled Nmap sample",
    severity: "critical",
    status: "in_progress",
    source: "Nmap",
    time: "2026-03-15 09:11"
  }
];

export const incidentRows = [
  {
    id: "INC-201",
    title: "Credential attack rehearsal review",
    priority: "high",
    owner: "Analyst Team",
    status: "in_progress",
    updated: "10 minutes ago"
  },
  {
    id: "INC-202",
    title: "Network anomaly validation",
    priority: "medium",
    owner: "Blue Lab",
    status: "triaged",
    updated: "32 minutes ago"
  },
  {
    id: "INC-203",
    title: "Endpoint hardening follow-up",
    priority: "low",
    owner: "Admin",
    status: "resolved",
    updated: "1 hour ago"
  }
];

export const reportRows = [
  {
    id: "REP-01",
    name: "Weekly SOC posture",
    type: "Executive summary",
    status: "ready",
    generatedBy: "Admin",
    schedule: "Every Friday"
  },
  {
    id: "REP-02",
    name: "Lab anomaly digest",
    type: "ML insights",
    status: "draft",
    generatedBy: "Analyst",
    schedule: "On demand"
  },
  {
    id: "REP-03",
    name: "Integration coverage",
    type: "Operational",
    status: "ready",
    generatedBy: "Viewer",
    schedule: "Every Monday"
  }
];

export const integrationRows = [
  {
    id: "INT-01",
    name: "Wazuh manager",
    status: "connected",
    mode: "Log ingestion",
    lastSync: "2 minutes ago"
  },
  {
    id: "INT-02",
    name: "Suricata sensor",
    status: "connected",
    mode: "Alert enrichment",
    lastSync: "5 minutes ago"
  },
  {
    id: "INT-03",
    name: "Nmap lab import",
    status: "pending",
    mode: "Safe result parsing",
    lastSync: "Awaiting sample file"
  },
  {
    id: "INT-04",
    name: "Hydra lab import",
    status: "pending",
    mode: "Simulation ingest",
    lastSync: "Awaiting sample file"
  }
];
