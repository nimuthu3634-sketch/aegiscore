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
    page: int
    page_size: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserRead"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class RoleRead(ORMModel):
    name: UserRole
    description: str


class UserRead(ORMModel):
    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    last_login_at: datetime | None = None
    created_at: datetime
    role_ref: RoleRead | None = None


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


class ResponseRecommendationRead(ORMModel):
    id: str
    title: str
    description: str | None
    priority: int
    created_at: datetime


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
    source_type: str
    event_type: str | None
    severity: AlertSeverity
    status: AlertStatus
    risk_score: float
    risk_label: str | None
    explainability: list
    explanation_summary: str | None
    recommendations: list[str] = Field(default_factory=list)
    occurred_at: datetime
    detected_at: datetime
    created_at: datetime
    updated_at: datetime
    tags: list[str] = Field(default_factory=list)
    incident_ids: list[str] = Field(default_factory=list)
    asset: AssetRead | None = None
    assignee: UserRead | None = None
    integration: "IntegrationRead | None" = None
    comments: list[AlertCommentRead] = Field(default_factory=list)
    response_recommendations: list[ResponseRecommendationRead] = Field(default_factory=list)


class AlertCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str | None = Field(default=None, max_length=8000)
    source: str = Field(min_length=2, max_length=50)
    source_type: str = Field(default="telemetry", min_length=2, max_length=50)
    event_type: str | None = Field(default=None, max_length=100)
    severity: AlertSeverity
    occurred_at: datetime | None = None
    asset_hostname: str | None = Field(default=None, max_length=255)
    asset_ip: str | None = Field(default=None, max_length=64)
    tags: list[str] = Field(default_factory=list)
    raw_payload: dict = Field(default_factory=dict)
    parsed_payload: dict = Field(default_factory=dict)


class AlertUpdate(BaseModel):
    status: AlertStatus | None = None
    severity: AlertSeverity | None = None
    assigned_to_id: str | None = None
    tags: list[str] | None = None
    explanation_summary: str | None = Field(default=None, max_length=4000)


class IncidentEventRead(ORMModel):
    id: str
    event_type: str
    body: str
    event_metadata: dict
    is_timeline_event: bool
    created_at: datetime
    author: UserRead | None = None


class IncidentEventCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
    event_type: str = Field(default="note", min_length=2, max_length=50)
    event_metadata: dict = Field(default_factory=dict)
    is_timeline_event: bool = True


class IncidentRead(ORMModel):
    id: str
    reference: str
    title: str
    description: str | None
    status: IncidentStatus
    priority: IncidentPriority
    opened_at: datetime
    resolved_at: datetime | None
    resolution_notes: str | None
    evidence: list[dict] = Field(default_factory=list)
    assignee: UserRead | None = None
    created_by: UserRead | None = None
    timeline_events: list[IncidentEventRead] = Field(default_factory=list, alias="events")
    linked_alerts: list[AlertRead] = Field(default_factory=list)


class IncidentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str | None = Field(default=None, max_length=8000)
    priority: IncidentPriority = IncidentPriority.P3
    assignee_id: str | None = None
    linked_alert_ids: list[str] = Field(default_factory=list)
    evidence: list[dict] = Field(default_factory=list)


class IncidentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = Field(default=None, max_length=8000)
    status: IncidentStatus | None = None
    priority: IncidentPriority | None = None
    assignee_id: str | None = None
    resolution_notes: str | None = Field(default=None, max_length=8000)
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
    runs: list[IntegrationRunRead] = Field(default_factory=list)


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


class RiskModelMetadataRead(ORMModel):
    id: str
    model_name: str
    version: str
    trained_at: datetime
    is_active: bool
    metrics: dict
    feature_names: list
    training_parameters: dict
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


class ServiceStatus(BaseModel):
    status: str
    latency_ms: float | None = None
    detail: str | None = None


class HealthResponse(BaseModel):
    app: ServiceStatus
    database: ServiceStatus
    redis: ServiceStatus


class AlertListResponse(PaginatedResponse[AlertRead]):
    pass


class IncidentListResponse(PaginatedResponse[IncidentRead]):
    pass


class LogEntryListResponse(PaginatedResponse[LogEntryRead]):
    pass


class AssetListResponse(PaginatedResponse[AssetRead]):
    pass


class IntegrationListResponse(PaginatedResponse[IntegrationRead]):
    pass


class IntegrationRunListResponse(PaginatedResponse[IntegrationRunRead]):
    pass


class AuditLogListResponse(PaginatedResponse[AuditLogRead]):
    pass


class UserListResponse(PaginatedResponse[UserRead]):
    pass


TokenResponse.model_rebuild()
AlertRead.model_rebuild()
IncidentRead.model_rebuild()
