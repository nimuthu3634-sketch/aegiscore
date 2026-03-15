export type SeverityLevel = "critical" | "high" | "medium" | "low";

export type AlertStatus = "new" | "triaged" | "investigating" | "resolved";

export type IncidentStatus = "open" | "triaged" | "in_progress" | "resolved";

export type AssignmentStatus = "assigned" | "unassigned" | "escalated";

export type ReportStatus = "draft" | "scheduled" | "ready";

export type IntegrationStatus = "connected" | "degraded" | "pending" | "offline";

export interface DashboardStat {
  label: string;
  value: string;
  change: string;
  helper: string;
  tone: "orange" | "dark" | "critical" | "success";
}

export interface AlertsTrendPoint {
  label: string;
  total: number;
}

export interface SeverityChartPoint {
  severity: string;
  count: number;
}

export interface AlertRecord {
  id: string;
  title: string;
  source: "Wazuh" | "Suricata" | "Nmap" | "Hydra" | "VirtualBox";
  asset: string;
  severity: SeverityLevel;
  status: AlertStatus;
  analyst: string;
  createdAt: string;
  description: string;
}

export interface IncidentRecord {
  id: string;
  title: string;
  priority: SeverityLevel;
  status: IncidentStatus;
  assignmentStatus: AssignmentStatus;
  analyst: string;
  affectedAsset: string;
  updatedAt: string;
  summary: string;
}

export interface ReportMetric {
  label: string;
  value: string;
  detail: string;
}

export interface ReportTrendPoint {
  label: string;
  incidents: number;
}

export interface ReportCategoryPoint {
  label: string;
  value: number;
}

export interface ReportRecord {
  id: string;
  name: string;
  owner: string;
  range: string;
  status: ReportStatus;
  generatedAt: string;
}

export interface IntegrationRecord {
  id: string;
  name: string;
  vendor: string;
  status: IntegrationStatus;
  description: string;
  lastSync: string;
  labOnly?: boolean;
  note?: string;
}

export interface SettingsItem {
  label: string;
  value: string;
  description: string;
}
