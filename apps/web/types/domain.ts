export type Role = "Admin" | "Analyst" | "Viewer";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  last_login_at?: string | null;
  created_at: string;
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

export interface AlertComment {
  id: string;
  body: string;
  created_at: string;
  author?: User | null;
}

export interface IntegrationRun {
  id: string;
  status: string;
  started_at: string;
  completed_at?: string | null;
  source_filename?: string | null;
  records_ingested: number;
  summary: Record<string, number>;
  error_message?: string | null;
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
  runs: IntegrationRun[];
}

export interface Alert {
  id: string;
  external_id?: string | null;
  title: string;
  description?: string | null;
  source: string;
  severity: string;
  status: string;
  risk_score: number;
  risk_label?: string | null;
  explainability: Array<{ factor: string; impact: number; value?: number }>;
  recommendations: string[];
  detected_at: string;
  tags: string[];
  asset?: Asset | null;
  assignee?: User | null;
  integration?: Integration | null;
  comments: AlertComment[];
}

export interface IncidentNote {
  id: string;
  body: string;
  is_timeline_event: boolean;
  created_at: string;
  author?: User | null;
}

export interface Incident {
  id: string;
  reference: string;
  title: string;
  summary?: string | null;
  status: string;
  priority: string;
  opened_at: string;
  resolved_at?: string | null;
  closure_summary?: string | null;
  evidence: Array<Record<string, string>>;
  assignee?: User | null;
  created_by?: User | null;
  notes: IncidentNote[];
  linked_alerts: Alert[];
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

export interface ModelMetadata {
  id: string;
  model_name: string;
  version: string;
  trained_at: string;
  is_active: boolean;
  metrics: Record<string, number>;
  feature_names: string[];
  notes?: string | null;
}

export interface PageResult<T> {
  items: T[];
  total: number;
}
