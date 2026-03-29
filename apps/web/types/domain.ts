export type Role = "Admin" | "Analyst" | "Viewer";

export interface RoleInfo {
  name: Role;
  description: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  last_login_at?: string | null;
  created_at: string;
  role_ref?: RoleInfo | null;
}

export interface Asset {
  id: string;
  hostname: string;
  ip_address?: string | null;
  operating_system?: string | null;
  business_unit?: string | null;
  criticality: number;
  risk_score: number;
  risk_summary?: string | null;
  last_seen_at?: string | null;
}

export interface ResponseRecommendation {
  id: string;
  title: string;
  description?: string | null;
  priority: number;
  created_at: string;
}

export interface AlertComment {
  id: string;
  body: string;
  created_at: string;
  author?: User | null;
}

export interface RiskExplanationFactor {
  factor: string;
  label?: string | null;
  detail?: string | null;
  impact: number;
  value?: number | null;
  category?: string | null;
}

export interface IntegrationRun {
  id: string;
  status: string;
  started_at: string;
  completed_at?: string | null;
  source_filename?: string | null;
  records_ingested: number;
  summary: Record<string, unknown>;
  error_message?: string | null;
  mode?: string | null;
  input_format?: string | null;
  alerts_created?: number;
  alerts_updated?: number;
  logs_created?: number;
  assets_touched?: number;
  incident_candidates?: number;
  normalized_records?: number;
  imported_lab_data?: boolean;
}

export interface IntegrationConfiguration {
  endpoint_url?: string | null;
  auth_type: string;
  username?: string | null;
  verify_tls: boolean;
  timeout_seconds: number;
  lookback_minutes: number;
  request_headers: Record<string, string>;
  query_params: Record<string, string>;
  has_password: boolean;
  has_api_token: boolean;
  configured: boolean;
  supports_manual_sync: boolean;
  supports_file_import: boolean;
  lab_only_import: boolean;
  supported_formats: string[];
}

export interface Integration {
  id: string;
  name: string;
  slug: string;
  type: string;
  health_status: string;
  enabled: boolean;
  description?: string | null;
  last_synced_at?: string | null;
  last_error?: string | null;
  connection_status?: string;
  status_detail?: string | null;
  consecutive_failures?: number;
  last_successful_sync_at?: string | null;
  supports_manual_sync?: boolean;
  supports_file_import?: boolean;
  lab_only_import?: boolean;
  supported_formats?: string[];
  configuration?: IntegrationConfiguration;
  runs: IntegrationRun[];
}

export interface Alert {
  id: string;
  external_id?: string | null;
  title: string;
  description?: string | null;
  source: string;
  source_type: string;
  event_type?: string | null;
  severity: string;
  status: string;
  risk_score: number;
  risk_label?: string | null;
  explainability: RiskExplanationFactor[];
  explanation_summary?: string | null;
  recommendations: string[];
  occurred_at: string;
  detected_at: string;
  created_at: string;
  updated_at: string;
  tags: string[];
  incident_ids: string[];
  asset?: Asset | null;
  assignee?: User | null;
  integration?: Integration | null;
  comments: AlertComment[];
  response_recommendations: ResponseRecommendation[];
}

export interface IncidentEvent {
  id: string;
  event_type: string;
  body: string;
  event_metadata: Record<string, unknown>;
  is_timeline_event: boolean;
  created_at: string;
  author?: User | null;
}

export interface Incident {
  id: string;
  reference: string;
  title: string;
  description?: string | null;
  status: string;
  priority: string;
  opened_at: string;
  resolved_at?: string | null;
  resolution_notes?: string | null;
  evidence: Array<Record<string, unknown>>;
  assignee?: User | null;
  created_by?: User | null;
  timeline_events: IncidentEvent[];
  linked_alerts: Alert[];
}

export interface LogEntry {
  id: string;
  source: string;
  level: string;
  category?: string | null;
  message: string;
  event_timestamp: string;
  raw_payload: Record<string, unknown>;
  parsed_payload: Record<string, unknown>;
  asset?: Asset | null;
}

export interface DashboardSummary {
  kpis: {
    total_assets: number;
    open_alerts: number;
    open_incidents: number;
    ingestion_today: number;
    average_risk_score: number;
  };
  severity_breakdown: Record<string, number>;
  integration_health: Record<string, string>;
  alert_trend: Array<{ label: string; critical: number; high: number; medium: number; low: number }>;
  risky_assets: Asset[];
  recent_activity: Array<{ id: string; timestamp: string; title: string; kind: string; summary: string }>;
}

export interface RiskModelMetadata {
  id: string;
  model_name: string;
  version: string;
  trained_at: string;
  is_active: boolean;
  metrics: Record<string, number>;
  feature_names: string[];
  training_parameters: Record<string, unknown>;
  notes?: string | null;
  feature_version?: string | null;
  performance_notes: string[];
}

export interface RiskOverview {
  active_model?: RiskModelMetadata | null;
  summary: {
    total_alerts: number;
    average_risk_score: number;
    high_priority_alerts: number;
    anomalous_alerts: number;
    correlated_source_alerts: number;
  };
  risk_distribution: Array<{ band: string; count: number }>;
  source_comparison: Array<{ source: string; alert_count: number; average_risk_score: number; anomalous_alerts: number }>;
  top_explanations: Array<{ factor: string; label: string; total_impact: number; alert_count: number }>;
  anomaly_trend: Array<{ label: string; average_risk_score: number; anomalous_alerts: number; critical_alerts: number }>;
}

export interface JobRecord {
  id: string;
  job_type: string;
  status: string;
  queued_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  result: Record<string, unknown>;
  error_message?: string | null;
}

export interface AuditLog {
  id: string;
  action: string;
  entity_type: string;
  entity_id?: string | null;
  details: Record<string, unknown>;
  ip_address?: string | null;
  created_at: string;
  actor?: User | null;
}

export interface ServiceStatus {
  status: string;
  latency_ms?: number | null;
  detail?: string | null;
}

export interface HealthResponse {
  app: ServiceStatus;
  database: ServiceStatus;
  redis: ServiceStatus;
}

export interface ImportResult {
  integration: string;
  run_id: string;
  mode: string;
  status: string;
  alerts_created: number;
  alerts_updated?: number;
  logs_created: number;
  assets_touched: number;
  incident_candidates: number;
  normalized_records?: number;
  input_format?: string | null;
  imported_lab_data?: boolean;
}

export interface PageResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
