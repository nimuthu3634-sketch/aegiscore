from __future__ import annotations

from datetime import datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from pydantic_core import PydanticCustomError

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
PASSWORD_POLICY_MESSAGE = "Password must include uppercase, lowercase, number, and symbol characters."


def validate_password_strength(value: str) -> str:
    if len(value) < 8:
        raise PydanticCustomError("password_too_short", "Password must be at least 8 characters.")
    if len(value) > 128:
        raise PydanticCustomError("password_too_long", "Password must be 128 characters or fewer.")
    checks = (
        any(character.islower() for character in value),
        any(character.isupper() for character in value),
        any(character.isdigit() for character in value),
        any(not character.isalnum() for character in value),
    )
    if not all(checks):
        raise PydanticCustomError("password_policy", PASSWORD_POLICY_MESSAGE)
    return value


def normalize_text(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise PydanticCustomError("blank_value", "This field cannot be blank.")
    return normalized


def validate_string_map(values: dict[str, str] | None) -> dict[str, str] | None:
    if values is None:
        return None
    cleaned: dict[str, str] = {}
    for key, value in values.items():
        normalized_key = normalize_text(str(key))
        normalized_value = str(value).strip()
        if "\n" in normalized_key or "\r" in normalized_key or "\n" in normalized_value or "\r" in normalized_value:
            raise PydanticCustomError(
                "invalid_string_map",
                "Header and query parameter values must be single-line strings.",
            )
        if len(normalized_key) > 100:
            raise PydanticCustomError("config_key_too_long", "Configuration keys must be 100 characters or fewer.")
        if len(normalized_value) > 500:
            raise PydanticCustomError(
                "config_value_too_long",
                "Configuration values must be 500 characters or fewer.",
            )
        cleaned[normalized_key] = normalized_value
    return cleaned


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
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


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
    full_name: str = Field(min_length=2, max_length=255)
    role: UserRole
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        return normalize_text(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_strength(value)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    role: UserRole | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    is_active: bool | None = None

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalize_text(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_password_strength(value)


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalize_text(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_password_strength(value)


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


class RiskExplanationFactorRead(BaseModel):
    factor: str
    label: str | None = None
    detail: str | None = None
    impact: float
    value: float | None = None
    category: str | None = None


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
    explainability: list[RiskExplanationFactorRead] = Field(default_factory=list)
    explanation_summary: str | None
    recommendations: list[str] = Field(default_factory=list)
    occurred_at: datetime
    detected_at: datetime
    created_at: datetime
    updated_at: datetime
    tags: list[str] = Field(default_factory=list)
    incident_ids: list[str] = Field(default_factory=list)
    asset: "AssetRead | None" = None
    assignee: "UserRead | None" = None
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


class ResponseActionRequest(BaseModel):
    action: Literal["block_ip", "isolate_asset", "disable_user", "contain_alert"]
    reason: str | None = Field(default=None, max_length=1000)

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class ResponseActionResult(BaseModel):
    alert_id: str
    action: str
    status: Literal["recorded", "simulated"]
    message: str
    executed_at: datetime
    target: dict[str, str | None] = Field(default_factory=dict)
    follow_up: list[str] = Field(default_factory=list)


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
    timeline_events: list[IncidentEventRead] = Field(default_factory=list, validation_alias="events")
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
    mode: str | None = None
    input_format: str | None = None
    alerts_created: int = 0
    alerts_updated: int = 0
    logs_created: int = 0
    assets_touched: int = 0
    incident_candidates: int = 0
    normalized_records: int = 0
    imported_lab_data: bool = False


class IntegrationConfigurationRead(BaseModel):
    endpoint_url: str | None = None
    auth_type: str = "none"
    username: str | None = None
    verify_tls: bool = True
    timeout_seconds: int = 15
    lookback_minutes: int = 60
    request_headers: dict[str, str] = Field(default_factory=dict)
    query_params: dict[str, str] = Field(default_factory=dict)
    has_password: bool = False
    has_api_token: bool = False
    configured: bool = False
    supports_manual_sync: bool = False
    supports_file_import: bool = True
    lab_only_import: bool = False
    supported_formats: list[str] = Field(default_factory=list)


class IntegrationConfigUpdate(BaseModel):
    enabled: bool | None = None
    endpoint_url: str | None = Field(default=None, max_length=500)
    auth_type: Literal["none", "bearer", "basic"] | None = None
    username: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, max_length=255)
    api_token: str | None = Field(default=None, max_length=500)
    verify_tls: bool | None = None
    timeout_seconds: int | None = Field(default=None, ge=1, le=120)
    lookback_minutes: int | None = Field(default=None, ge=1, le=1440)
    request_headers: dict[str, str] | None = None
    query_params: dict[str, str] | None = None

    @field_validator("endpoint_url")
    @classmethod
    def validate_endpoint_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized.startswith(("http://", "https://")):
            raise PydanticCustomError("endpoint_url_scheme", "Endpoint URL must start with http:// or https://")
        return normalized.rstrip("/")

    @field_validator("username", "password", "api_token")
    @classmethod
    def strip_credentials(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("request_headers", "query_params")
    @classmethod
    def validate_maps(cls, value: dict[str, str] | None) -> dict[str, str] | None:
        return validate_string_map(value)


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
    connection_status: str
    status_detail: str | None
    consecutive_failures: int = 0
    last_successful_sync_at: datetime | None = None
    supports_manual_sync: bool = False
    supports_file_import: bool = True
    lab_only_import: bool = False
    supported_formats: list[str] = Field(default_factory=list)
    configuration: IntegrationConfigurationRead = Field(validation_alias="sanitized_config")
    runs: list[IntegrationRunRead] = Field(default_factory=list)


class ImportResult(BaseModel):
    integration: str
    run_id: str
    mode: str
    status: str
    alerts_created: int
    alerts_updated: int = 0
    logs_created: int
    assets_touched: int
    incident_candidates: int
    normalized_records: int = 0
    input_format: str | None = None
    imported_lab_data: bool = False


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
    feature_version: str | None = None
    performance_notes: list[str] = Field(default_factory=list)


class RetrainResponse(BaseModel):
    job_id: str
    status: JobStatus


class RiskOverviewSummary(BaseModel):
    total_alerts: int
    average_risk_score: float
    high_priority_alerts: int
    anomalous_alerts: int
    correlated_source_alerts: int


class RiskDistributionItem(BaseModel):
    band: str
    count: int


class RiskSourceComparisonItem(BaseModel):
    source: str
    alert_count: int
    average_risk_score: float
    anomalous_alerts: int


class RiskExplanationAggregate(BaseModel):
    factor: str
    label: str
    total_impact: float
    alert_count: int


class RiskTrendPoint(BaseModel):
    label: str
    average_risk_score: float
    anomalous_alerts: int
    critical_alerts: int


class RiskOverviewRead(BaseModel):
    active_model: RiskModelMetadataRead | None = None
    summary: RiskOverviewSummary
    risk_distribution: list[RiskDistributionItem] = Field(default_factory=list)
    source_comparison: list[RiskSourceComparisonItem] = Field(default_factory=list)
    top_explanations: list[RiskExplanationAggregate] = Field(default_factory=list)
    anomaly_trend: list[RiskTrendPoint] = Field(default_factory=list)


class ScoreRecalculationRequest(BaseModel):
    source: str | None = Field(default=None, max_length=50)
    open_only: bool = True
    limit: int | None = Field(default=None, ge=1, le=1000)


class ScoreRecalculationResponse(BaseModel):
    rescored_alerts: int
    updated_assets: int


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
