from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.entities import (
    AlertSeverity,
    AlertStatus,
    IncidentPriority,
    IncidentStatus,
    IntegrationHealth,
    IntegrationType,
    JobStatus,
    UserRole,
)

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(ORMModel, Generic[T]):
    items: list[T]
    total: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserRead"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserRead(ORMModel):
    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    last_login_at: datetime | None = None
    created_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole
    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None
    password: str | None = Field(default=None, min_length=8)
    is_active: bool | None = None


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    password: str | None = Field(default=None, min_length=8)


class AuditLogRead(ORMModel):
    id: str
    action: str
    entity_type: str
    entity_id: str | None
    details: dict
    ip_address: str | None
    created_at: datetime
    actor: UserRead | None = None


class AssetRead(ORMModel):
    id: str
    hostname: str
    ip_address: str | None
    operating_system: str | None
    business_unit: str | None
    criticality: int
    risk_score: float
    risk_summary: str | None
    last_seen_at: datetime | None


class AlertCommentRead(ORMModel):
    id: str
    body: str
    created_at: datetime
    author: UserRead | None = None


class AlertCommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class AlertRead(ORMModel):
    id: str
    external_id: str | None
    title: str
    description: str | None
    source: str
    severity: AlertSeverity
    status: AlertStatus
    risk_score: float
    risk_label: str | None
    explainability: list
    recommendations: list
    detected_at: datetime
    tags: list
    asset: AssetRead | None = None
    assignee: UserRead | None = None
    integration: "IntegrationRead | None" = None
    comments: list[AlertCommentRead] = []


class AlertCreate(BaseModel):
    title: str
    description: str | None = None
    source: str
    severity: AlertSeverity
    asset_hostname: str | None = None
    asset_ip: str | None = None
    tags: list[str] = []
    raw_payload: dict = Field(default_factory=dict)
    parsed_payload: dict = Field(default_factory=dict)


class AlertUpdate(BaseModel):
    status: AlertStatus | None = None
    severity: AlertSeverity | None = None
    assigned_to_id: str | None = None
    tags: list[str] | None = None


class IncidentNoteRead(ORMModel):
    id: str
    body: str
    is_timeline_event: bool
    created_at: datetime
    author: UserRead | None = None


class IncidentNoteCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
    is_timeline_event: bool = False


class IncidentRead(ORMModel):
    id: str
    reference: str
    title: str
    summary: str | None
    status: IncidentStatus
    priority: IncidentPriority
    opened_at: datetime
    resolved_at: datetime | None
    closure_summary: str | None
    evidence: list
    assignee: UserRead | None = None
    created_by: UserRead | None = None
    notes: list[IncidentNoteRead] = []
    linked_alerts: list[AlertRead] = []


class IncidentCreate(BaseModel):
    title: str
    summary: str | None = None
    priority: IncidentPriority = IncidentPriority.P3
    assignee_id: str | None = None
    linked_alert_ids: list[str] = []
    evidence: list[dict] = []


class IncidentUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    status: IncidentStatus | None = None
    priority: IncidentPriority | None = None
    assignee_id: str | None = None
    closure_summary: str | None = None
    evidence: list[dict] | None = None


class LogEntryRead(ORMModel):
    id: str
    source: str
    level: str
    category: str | None
    message: str
    event_timestamp: datetime
    raw_payload: dict
    parsed_payload: dict
    asset: AssetRead | None = None


class IntegrationRunRead(ORMModel):
    id: str
    status: str
    started_at: datetime
    completed_at: datetime | None
    source_filename: str | None
    records_ingested: int
    summary: dict
    error_message: str | None


class IntegrationRead(ORMModel):
    id: str
    name: str
    slug: str
    type: IntegrationType
    health_status: IntegrationHealth
    enabled: bool
    description: str | None
    last_synced_at: datetime | None
    last_error: str | None
    runs: list[IntegrationRunRead] = []


class ImportResult(BaseModel):
    integration: str
    run_id: str
    alerts_created: int
    logs_created: int
    assets_touched: int
    incident_candidates: int


class DashboardKpi(BaseModel):
    total_assets: int
    open_alerts: int
    open_incidents: int
    ingestion_today: int
    average_risk_score: float


class DashboardTrendPoint(BaseModel):
    label: str
    critical: int
    high: int
    medium: int
    low: int


class DashboardActivityItem(BaseModel):
    id: str
    timestamp: datetime
    title: str
    kind: str
    summary: str


class DashboardSummary(BaseModel):
    kpis: DashboardKpi
    severity_breakdown: dict[str, int]
    integration_health: dict[str, str]
    alert_trend: list[DashboardTrendPoint]
    risky_assets: list[AssetRead]
    recent_activity: list[DashboardActivityItem]


class ModelMetadataRead(ORMModel):
    id: str
    model_name: str
    version: str
    trained_at: datetime
    is_active: bool
    metrics: dict
    feature_names: list
    notes: str | None


class RetrainResponse(BaseModel):
    job_id: str
    status: JobStatus


class JobRead(ORMModel):
    id: str
    job_type: str
    status: JobStatus
    queued_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    result: dict
    error_message: str | None


TokenResponse.model_rebuild()
AlertRead.model_rebuild()
IncidentRead.model_rebuild()
