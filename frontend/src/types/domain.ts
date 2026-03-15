export type SeverityLevel = "critical" | "high" | "medium" | "low";

export type AlertStatus = "new" | "triaged" | "investigating" | "resolved";

export type IncidentStatus = "open" | "triaged" | "in_progress" | "resolved";

export type AssignmentStatus = "assigned" | "unassigned" | "escalated";

export type ReportStatus = "draft" | "scheduled" | "ready";

export type IntegrationStatus = "connected" | "degraded" | "pending" | "offline";

export type SourceToolKey = "wazuh" | "suricata" | "nmap" | "hydra" | "virtualbox";

export type VirtualMachineStatus = "running" | "stopped" | "paused" | "provisioning";

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

export interface IncidentAssigneeOption {
  id: string;
  full_name: string;
  email: string;
  role: "admin" | "analyst" | "viewer";
}

export interface IncidentApiRecord {
  id: string;
  alert_id: string | null;
  alert_title: string | null;
  title: string;
  priority: SeverityLevel;
  status: IncidentStatus;
  notes: string;
  opened_at: string;
  updated_at: string;
  closed_at: string | null;
  assigned_to_user_id: string | null;
  assigned_to_name: string | null;
  affected_asset: string;
  source_tool: SourceToolKey | null;
  summary: string;
}

export interface IncidentListResponse {
  items: IncidentApiRecord[];
  available_assignees: IncidentAssigneeOption[];
  total_items: number;
}

export interface IncidentFilters {
  priority?: SeverityLevel;
  status?: IncidentStatus;
  assignee_id?: string;
}

export interface IncidentCreatePayload {
  alert_id: string;
  assigned_to_user_id?: string | null;
  priority?: SeverityLevel;
  notes?: string;
}

export interface IncidentUpdatePayload {
  assigned_to_user_id?: string | null;
  priority?: SeverityLevel;
  status?: IncidentStatus;
  notes?: string;
}

export interface LogEntryRecord {
  id: string;
  source: string;
  source_tool: string;
  raw_log: Record<string, unknown>;
  normalized_log: Record<string, unknown>;
  event_type: string;
  severity: SeverityLevel;
  created_at: string;
}

export interface LogListResponse {
  items: LogEntryRecord[];
  total_items: number;
}

export interface LogIngestPayload {
  source?: string;
  source_tool: string;
  raw_log: Record<string, unknown>;
  timestamp?: string | number;
  severity?: string | number;
  event_type?: string;
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

export interface IntegrationApiRecord {
  id: string;
  tool_name: SourceToolKey;
  status: IntegrationStatus;
  last_sync_at: string;
  notes: string;
  imported_alert_count: number;
  imported_log_count: number;
  last_import_at: string | null;
  last_import_message: string | null;
}

export interface IntegrationImportStatus extends IntegrationApiRecord {
  available_demo_payloads: number;
  latest_imported_alert_titles: string[];
}

export interface IntegrationImportResponse {
  imported_alert_count: number;
  imported_log_count: number;
  skipped_count: number;
  last_import_at: string;
  message: string;
}

export interface WazuhIntegrationStatus extends IntegrationImportStatus {}

export interface WazuhImportPayload {
  alerts: Record<string, unknown>[];
}

export interface WazuhImportResponse extends IntegrationImportResponse {}

export interface SuricataIntegrationStatus extends IntegrationImportStatus {}

export interface SuricataImportPayload {
  events: Record<string, unknown>[];
}

export interface SuricataImportResponse extends IntegrationImportResponse {}

export interface NmapPortResult {
  port: number;
  service_name?: string | null;
  protocol?: string;
  state?: string;
}

export interface NmapImportItem {
  host: string;
  open_ports: NmapPortResult[];
  service_names: string[];
  scan_timestamp?: string | number | null;
  scan_notes?: string | null;
}

export interface NmapImportPayload {
  results: NmapImportItem[];
}

export interface NmapIntegrationStatus extends IntegrationImportStatus {}

export interface NmapImportResponse extends IntegrationImportResponse {}

export interface HydraImportItem {
  target_system: string;
  protocol: string;
  result_summary: string;
  timestamp?: string | number | null;
  notes?: string | null;
}

export interface HydraImportPayload {
  results: HydraImportItem[];
}

export interface HydraIntegrationStatus extends IntegrationImportStatus {}

export interface HydraImportResponse extends IntegrationImportResponse {}

export interface VirtualMachineRecord {
  id: string;
  vm_name: string;
  role: string;
  os_type: string;
  ip_address: string;
  status: VirtualMachineStatus;
  notes: string;
}

export interface VirtualMachineCreatePayload {
  vm_name: string;
  role: string;
  os_type: string;
  ip_address: string;
  status: VirtualMachineStatus;
  notes: string;
}

export interface VirtualMachineUpdatePayload {
  vm_name?: string;
  role?: string;
  os_type?: string;
  ip_address?: string;
  status?: VirtualMachineStatus;
  notes?: string;
}

export interface SettingsItem {
  label: string;
  value: string;
  description: string;
}
