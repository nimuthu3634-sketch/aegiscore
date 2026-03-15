import type {
  AlertRecord,
  AlertsTrendPoint,
  DashboardStat,
  IncidentRecord,
  IntegrationRecord,
  ReportCategoryPoint,
  ReportMetric,
  ReportRecord,
  ReportTrendPoint,
  SeverityChartPoint,
  SettingsItem,
} from "@/types/domain";

export const dashboardStats: DashboardStat[] = [
  {
    label: "Total Alerts",
    value: "128",
    change: "+14 today",
    helper: "Across all lab integrations",
    tone: "orange",
  },
  {
    label: "Critical Alerts",
    value: "09",
    change: "4 unassigned",
    helper: "Immediate analyst attention",
    tone: "critical",
  },
  {
    label: "Open Incidents",
    value: "12",
    change: "3 escalated",
    helper: "Case workflow in progress",
    tone: "dark",
  },
  {
    label: "Resolved Incidents",
    value: "34",
    change: "+8 this week",
    helper: "Operational closure trend",
    tone: "success",
  },
];

export const alertsOverTime: AlertsTrendPoint[] = [
  { label: "Mon", total: 18 },
  { label: "Tue", total: 24 },
  { label: "Wed", total: 31 },
  { label: "Thu", total: 28 },
  { label: "Fri", total: 34 },
  { label: "Sat", total: 20 },
  { label: "Sun", total: 27 },
];

export const alertsBySeverity: SeverityChartPoint[] = [
  { severity: "Critical", count: 9 },
  { severity: "High", count: 28 },
  { severity: "Medium", count: 41 },
  { severity: "Low", count: 50 },
];

export const alerts: AlertRecord[] = [
  {
    id: "ALT-1001",
    title: "Repeated SSH authentication failures",
    source: "Wazuh",
    asset: "lab-web-01",
    severity: "high",
    status: "new",
    analyst: "Unassigned",
    createdAt: "2026-03-15 10:24",
    description:
      "Wazuh reported repeated failed login attempts from a lab subnet against the web server.",
  },
  {
    id: "ALT-1002",
    title: "Suspicious DNS burst from analyst VLAN",
    source: "Suricata",
    asset: "sensor-east-02",
    severity: "medium",
    status: "triaged",
    analyst: "M. Perera",
    createdAt: "2026-03-15 10:07",
    description:
      "Suricata flagged an unusual volume of DNS requests for validation in the lab environment.",
  },
  {
    id: "ALT-1003",
    title: "Lab Hydra import exceeded threshold",
    source: "Hydra",
    asset: "simulation-node-01",
    severity: "low",
    status: "resolved",
    analyst: "K. Fernando",
    createdAt: "2026-03-15 09:48",
    description:
      "Authorized Hydra result ingestion produced elevated failed-attempt counts for analyst review.",
  },
  {
    id: "ALT-1004",
    title: "Unexpected service exposure in scan results",
    source: "Nmap",
    asset: "lab-gateway-01",
    severity: "critical",
    status: "investigating",
    analyst: "A. Silva",
    createdAt: "2026-03-15 09:11",
    description:
      "Imported Nmap lab output shows an exposed service that requires analyst validation and case review.",
  },
  {
    id: "ALT-1005",
    title: "VirtualBox snapshot drift detected",
    source: "VirtualBox",
    asset: "sandbox-host-03",
    severity: "medium",
    status: "triaged",
    analyst: "R. Jayasinghe",
    createdAt: "2026-03-15 08:56",
    description:
      "A VirtualBox training image snapshot drifted from the approved secure baseline.",
  },
  {
    id: "ALT-1006",
    title: "Kernel policy mismatch on endpoint",
    source: "Wazuh",
    asset: "endpoint-lab-07",
    severity: "high",
    status: "resolved",
    analyst: "M. Perera",
    createdAt: "2026-03-15 08:21",
    description:
      "Wazuh detected a policy mismatch during endpoint hardening checks on a lab workstation.",
  },
];

export const incidents: IncidentRecord[] = [
  {
    id: "INC-201",
    title: "Credential attack rehearsal review",
    priority: "high",
    status: "in_progress",
    assignmentStatus: "assigned",
    analyst: "A. Silva",
    affectedAsset: "lab-web-01",
    updatedAt: "10 minutes ago",
    summary:
      "Assess imported Hydra result artifacts and confirm the alert sequence aligns with the lab exercise scope.",
  },
  {
    id: "INC-202",
    title: "Northbound DNS anomaly validation",
    priority: "medium",
    status: "triaged",
    assignmentStatus: "assigned",
    analyst: "M. Perera",
    affectedAsset: "sensor-east-02",
    updatedAt: "32 minutes ago",
    summary:
      "Review traffic telemetry, correlate with Suricata alerts, and prepare an analyst narrative for reporting.",
  },
  {
    id: "INC-203",
    title: "Endpoint hardening follow-up",
    priority: "low",
    status: "resolved",
    assignmentStatus: "escalated",
    analyst: "Admin Review",
    affectedAsset: "endpoint-lab-07",
    updatedAt: "1 hour ago",
    summary:
      "Document remediation evidence and track final approval before archiving the case as complete.",
  },
  {
    id: "INC-204",
    title: "Snapshot integrity investigation",
    priority: "medium",
    status: "open",
    assignmentStatus: "unassigned",
    analyst: "Needs assignment",
    affectedAsset: "sandbox-host-03",
    updatedAt: "2 hours ago",
    summary:
      "Validate whether the VirtualBox baseline drift was expected or caused by a configuration deviation.",
  },
];

export const reportMetrics: ReportMetric[] = [
  { label: "Reports Generated", value: "24", detail: "Last 30 days" },
  { label: "Avg. Build Time", value: "02m 14s", detail: "Export generation" },
  { label: "Critical Cases Included", value: "11", detail: "Executive focus" },
];

export const reportTrend: ReportTrendPoint[] = [
  { label: "Week 1", incidents: 6 },
  { label: "Week 2", incidents: 8 },
  { label: "Week 3", incidents: 9 },
  { label: "Week 4", incidents: 7 },
];

export const reportCategories: ReportCategoryPoint[] = [
  { label: "Alerts", value: 32 },
  { label: "Incidents", value: 18 },
  { label: "Compliance", value: 11 },
  { label: "Anomalies", value: 15 },
];

export const reports: ReportRecord[] = [
  {
    id: "REP-01",
    name: "Weekly SOC executive summary",
    owner: "Admin Console",
    range: "2026-03-08 to 2026-03-15",
    status: "ready",
    generatedAt: "2026-03-15 09:40",
  },
  {
    id: "REP-02",
    name: "Analyst triage digest",
    owner: "M. Perera",
    range: "2026-03-01 to 2026-03-15",
    status: "draft",
    generatedAt: "2026-03-15 08:05",
  },
  {
    id: "REP-03",
    name: "Lab anomaly overview",
    owner: "A. Silva",
    range: "2026-02-15 to 2026-03-15",
    status: "scheduled",
    generatedAt: "Next run 2026-03-18",
  },
];

export const integrations: IntegrationRecord[] = [
  {
    id: "INT-01",
    name: "Wazuh",
    vendor: "Endpoint telemetry",
    status: "connected",
    description: "Centralized endpoint monitoring and alert enrichment for lab hosts.",
    lastSync: "2 minutes ago",
  },
  {
    id: "INT-02",
    name: "Suricata",
    vendor: "Network IDS",
    status: "connected",
    description: "Network alert stream with packet-inspection context and severity mapping.",
    lastSync: "5 minutes ago",
  },
  {
    id: "INT-03",
    name: "Nmap",
    vendor: "Lab result ingestion",
    status: "connected",
    description: "Parses authorized lab scan-result imports for assessment visualization only.",
    lastSync: "Awaiting sample file",
    labOnly: true,
    note: "Authorized assessment result ingestion",
  },
  {
    id: "INT-04",
    name: "Hydra",
    vendor: "Lab result ingestion",
    status: "connected",
    description: "Displays authorized lab credential-assessment imports from controlled simulations only.",
    lastSync: "Awaiting sample file",
    labOnly: true,
    note: "Authorized assessment result ingestion",
  },
  {
    id: "INT-05",
    name: "VirtualBox",
    vendor: "Lab infrastructure",
    status: "degraded",
    description: "Tracks the VirtualBox VM inventory, baseline state, and environment readiness without direct VM control.",
    lastSync: "15 minutes ago",
  },
];

export const brandingSettings: SettingsItem[] = [
  {
    label: "Primary Accent",
    value: "#FF7A1A",
    description: "Buttons, chart accents, active navigation, and status highlights.",
  },
  {
    label: "Sidebar Surface",
    value: "#1A1A1A",
    description: "Dark operational shell used for the main left navigation.",
  },
  {
    label: "Workspace Background",
    value: "#F3F3F3",
    description: "Light content surface that keeps dense dashboard data readable.",
  },
];

export const accountSettings: SettingsItem[] = [
  {
    label: "Display Name",
    value: "Admin Console",
    description: "Placeholder account profile for the current operating session.",
  },
  {
    label: "Role",
    value: "Admin",
    description: "Role-based access placeholder until backend JWT wiring is connected.",
  },
  {
    label: "Workspace",
    value: "AegisCore SOC",
    description: "Current team environment for cybersecurity operations monitoring.",
  },
];

export const systemConfig: SettingsItem[] = [
  {
    label: "API Mode",
    value: "Dashboard API connected",
    description: "Authentication and dashboard views are wired to the backend while other pages remain scaffolded.",
  },
  {
    label: "Realtime Feed",
    value: "Placeholder",
    description: "WebSocket stream can later power notifications, status tiles, and case updates.",
  },
  {
    label: "Export Mode",
    value: "Manual trigger",
    description: "Reports are scaffolded with UI controls and mock output rows.",
  },
];
