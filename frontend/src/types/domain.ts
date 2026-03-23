export type SeverityLevel = "critical" | "high" | "medium" | "low";

export type AlertStatus = "new" | "triaged" | "investigating" | "resolved";

export type IncidentStatus = "open" | "triaged" | "in_progress" | "resolved";

export type ResponseActionType =
  | "create_incident"
  | "block_source_ip"
  | "isolate_asset"
  | "disable_account"
  | "mark_investigating";

export type ResponseActionStatus = "completed" | "skipped";

export type ResponseActionMode = "automated" | "manual";

export type AssignmentStatus = "assigned" | "unassigned" | "escalated";

export type ReportStatus = "draft" | "scheduled" | "ready";

export type ReportType = "executive" | "incident" | "operations" | "analytics";

export type IntegrationStatus = "connected" | "degraded" | "pending" | "offline";

export type SourceToolKey = "wazuh" | "suricata" | "nmap" | "hydra" | "lanl" | "virtualbox";

export type LanlDatasetType = "auth" | "dns" | "flows";

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

export interface DashboardAnomalySummaryResponse {
  model_name: string;
  trained_on_events: number;
  feature_labels: string[];
  trained_at: string;
  average_anomaly_score: number;
  anomalous_alert_count: number;
  high_anomaly_alert_count: number;
  top_anomalous_alerts: AlertApiRecord[];
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
  anomaly_score: number;
  is_anomalous: boolean;
  anomaly_explanation: string;
  created_at: string;
}

export interface AlertApiRecord {
  id: string;
  title: string;
  description: string;
  source: string;
  source_tool: SourceToolKey;
  event_type: string;
  severity: SeverityLevel;
  status: AlertStatus;
  confidence_score: number;
  anomaly_score: number;
  is_anomalous: boolean;
  anomaly_explanation: string;
  integration_ref: string | null;
  parser_status: string | null;
  lab_only: boolean;
  finding_metadata: Record<string, unknown>;
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
  event_type?: string;
  page?: number;
  page_size?: number;
}

export interface AlertStatusUpdatePayload {
  status: AlertStatus;
}

export interface ResponseActionSuggestion {
  action_type: ResponseActionType;
  label: string;
  description: string;
  target_label: string | null;
  available: boolean;
  automated: boolean;
}

export interface ResponseActionRecord {
  id: string;
  alert_id: string;
  action_type: ResponseActionType;
  status: ResponseActionStatus;
  execution_mode: ResponseActionMode;
  target_label: string | null;
  notes: string;
  result_summary: string;
  performed_by_user_id: string | null;
  performed_by_name: string;
  incident_id: string | null;
  created_at: string;
}

export interface AlertResponseActionsResponse {
  items: ResponseActionRecord[];
  recommended_actions: ResponseActionSuggestion[];
}

export interface ResponseActionExecutePayload {
  action_type: ResponseActionType;
  notes?: string;
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
  alert_event_type: string | null;
  alert_anomaly_score: number | null;
  alert_is_anomalous: boolean | null;
  alert_parser_status: string | null;
  alert_integration_ref: string | null;
  alert_lab_only: boolean;
  alert_finding_metadata: Record<string, unknown>;
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
  integration_ref: string | null;
  parser_status: string | null;
  lab_only: boolean;
  finding_metadata: Record<string, unknown>;
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

export interface ReportSeverityPoint {
  severity: SeverityLevel;
  count: number;
}

export interface ReportSourceToolPoint {
  source_tool: SourceToolKey;
  count: number;
}

export interface ReportIncidentStatusPoint {
  status: IncidentStatus;
  count: number;
}

export interface ReportsAnomalySummary {
  model_name: string;
  trained_on_events: number;
  feature_labels: string[];
  trained_at: string;
  average_anomaly_score: number;
  anomalous_alert_count: number;
  high_anomaly_alert_count: number;
  top_anomalous_alerts: AlertApiRecord[];
}

export interface ReportsSummaryResponse {
  date_from: string | null;
  date_to: string | null;
  reports_generated: number;
  draft_reports: number;
  ready_reports: number;
  filtered_alert_count: number;
  filtered_incident_count: number;
  alerts_by_severity: ReportSeverityPoint[];
  alerts_by_source_tool: ReportSourceToolPoint[];
  incidents_by_status: ReportIncidentStatusPoint[];
  anomaly_summary: ReportsAnomalySummary;
}

export interface ReportSummarySnapshot {
  reports_generated: number;
  draft_reports: number;
  ready_reports: number;
  filtered_alert_count: number;
  filtered_incident_count: number;
  anomalous_alert_count: number;
  high_anomaly_alert_count: number;
  average_anomaly_score: number;
}

export interface ReportContentDateRange {
  date_from: string | null;
  date_to: string | null;
}

export interface ReportContentSnapshot {
  date_range: ReportContentDateRange;
  summary: ReportSummarySnapshot;
  alerts_by_severity: ReportSeverityPoint[];
  alerts_by_source_tool: ReportSourceToolPoint[];
  incidents_by_status: ReportIncidentStatusPoint[];
  anomaly_summary: ReportsAnomalySummary;
}

export interface ReportApiRecord {
  id: string;
  title: string;
  report_type: ReportType;
  generated_by_user_id: string | null;
  generated_by_name: string | null;
  content_json: ReportContentSnapshot;
  status: ReportStatus;
  created_at: string;
}

export interface ReportFilters {
  date_from?: string;
  date_to?: string;
}

export interface ReportGeneratePayload extends ReportFilters {
  title?: string;
  report_type: ReportType;
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

export interface LanlIntegrationStatus {
  tool_name: "lanl";
  status: IntegrationStatus;
  last_sync_at: string | null;
  notes: string;
  imported_alert_count: number;
  imported_log_count: number;
  last_import_at: string | null;
  last_import_message: string | null;
  supported_dataset_types: LanlDatasetType[];
  redteam_supported: boolean;
  latest_imported_alert_titles: string[];
}

export interface LanlImportResponse extends IntegrationImportResponse {
  dataset_type: LanlDatasetType;
  processed_record_count: number;
  redteam_match_count: number;
}

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
