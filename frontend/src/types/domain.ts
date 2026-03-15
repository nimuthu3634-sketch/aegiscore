export type SeverityLevel = "critical" | "high" | "medium" | "low";

export type AlertStatus = "new" | "triaged" | "investigating" | "resolved";

export type IncidentStatus = "open" | "triaged" | "in_progress" | "resolved";

export type AssignmentStatus = "assigned" | "unassigned" | "escalated";

export type ReportStatus = "draft" | "scheduled" | "ready";

export type IntegrationStatus = "connected" | "degraded" | "pending" | "offline";

export type SourceToolKey = "wazuh" | "suricata" | "nmap" | "hydra" | "virtualbox";

export interface DashboardSummaryResponse {
  total_alerts: number;
  critical_alerts: number;
  open_incidents: number;
  resolved_incidents: number;
}

export interface DashboardAlertsOverTimePoint {
  label: string;
  total: number;
}

export interface DashboardSeverityChartPoint {
  severity: SeverityLevel;
  count: number;
}

export interface DashboardSourceToolChartPoint {
  source_tool: SourceToolKey;
  count: number;
}

export interface DashboardChartsResponse {
  alerts_over_time: DashboardAlertsOverTimePoint[];
  alerts_by_severity: DashboardSeverityChartPoint[];
  alerts_by_source_tool: DashboardSourceToolChartPoint[];
}

export interface DashboardRecentAlert {
  id: string;
  title: string;
  description: string;
  source: string;
  source_tool: SourceToolKey;
  severity: SeverityLevel;
  status: AlertStatus;
  confidence_score: number;
  created_at: string;
}

export interface AlertApiRecord {
  id: string;
  title: string;
  description: string;
  source: string;
  source_tool: SourceToolKey;
  severity: SeverityLevel;
  status: AlertStatus;
  confidence_score: number;
  created_at: string;
}

export interface AlertListResponse {
  items: AlertApiRecord[];
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface AlertFilters {
  search?: string;
  severity?: SeverityLevel;
  status?: AlertStatus;
  source_tool?: SourceToolKey;
  page?: number;
  page_size?: number;
}

export interface AlertStatusUpdatePayload {
  status: AlertStatus;
}

export interface DashboardRecentIncident {
  id: string;
  title: string;
  priority: SeverityLevel;
  status: IncidentStatus;
  analyst_name: string | null;
  affected_asset: string;
  summary: string;
  updated_at: string;
}

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
