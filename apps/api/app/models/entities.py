from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def make_id() -> str:
    return str(uuid4())


class UserRole(str, Enum):
    ADMIN = "Admin"
    ANALYST = "Analyst"
    VIEWER = "Viewer"


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AlertStatus(str, Enum):
    OPEN = "open"
    TRIAGED = "triaged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class IncidentStatus(str, Enum):
    OPEN = "open"
    CONTAINED = "contained"
    MONITORING = "monitoring"
    RESOLVED = "resolved"


class IncidentPriority(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class IntegrationType(str, Enum):
    WAZUH = "wazuh"
    SURICATA = "suricata"
    NMAP = "nmap"
    HYDRA = "hydra"


class IntegrationHealth(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OFFLINE = "offline"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Role(Base):
    __tablename__ = "roles"

    name: Mapped[UserRole] = mapped_column(String(20), primary_key=True)
    description: Mapped[str] = mapped_column(String(255))

    users: Mapped[list["User"]] = relationship(back_populates="role_ref")


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=make_id)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(ForeignKey("roles.name"), default=UserRole.ANALYST, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    role_ref: Mapped[Role] = relationship(back_populates="users")
    assigned_alerts: Mapped[list["Alert"]] = relationship(back_populates="assignee", foreign_keys="Alert.assigned_to_id")
    assigned_incidents: Mapped[list["Incident"]] = relationship(
        back_populates="assignee", foreign_keys="Incident.assignee_id"
    )


class Asset(TimestampMixin, Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=make_id)
    hostname: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    operating_system: Mapped[str | None] = mapped_column(String(255), nullable=True)
    business_unit: Mapped[str | None] = mapped_column(String(255), nullable=True)
    criticality: Mapped[int] = mapped_column(Integer, default=3)
    risk_score: Mapped[float] = mapped_column(Float, default=0)
    risk_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    alerts: Mapped[list["Alert"]] = relationship(back_populates="asset")
    logs: Mapped[list["LogEntry"]] = relationship(back_populates="asset")


class Integration(TimestampMixin, Base):
    __tablename__ = "integrations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=make_id)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    type: Mapped[IntegrationType] = mapped_column(String(20))
    health_status: Mapped[IntegrationHealth] = mapped_column(String(20), default=IntegrationHealth.HEALTHY)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict)

    alerts: Mapped[list["Alert"]] = relationship(back_populates="integration")
    logs: Mapped[list["LogEntry"]] = relationship(back_populates="integration")
    runs: Mapped[list["IntegrationRun"]] = relationship(back_populates="integration", cascade="all, delete-orphan")

    @property
    def supports_manual_sync(self) -> bool:
        return self.slug in {IntegrationType.WAZUH.value, IntegrationType.SURICATA.value}

    @property
    def supports_file_import(self) -> bool:
        return True

    @property
    def lab_only_import(self) -> bool:
        return self.slug in {IntegrationType.NMAP.value, IntegrationType.HYDRA.value}

    @property
    def supported_formats(self) -> list[str]:
        mapping = {
            IntegrationType.WAZUH.value: ["json", "ndjson"],
            IntegrationType.SURICATA.value: ["json", "ndjson"],
            IntegrationType.NMAP.value: ["json", "xml"],
            IntegrationType.HYDRA.value: ["json", "ndjson", "txt"],
        }
        return mapping.get(self.slug, ["json"])

    @property
    def connection_status(self) -> str:
        if not self.enabled:
            return "disabled"
        if self.lab_only_import:
            return "import_only"
        if not (self.config or {}).get("endpoint_url"):
            return "needs_configuration"
        if self.health_status == IntegrationHealth.HEALTHY:
            return "connected"
        if self.health_status == IntegrationHealth.DEGRADED:
            return "degraded"
        if self.last_error:
            return "error"
        return "configured"

    @property
    def status_detail(self) -> str | None:
        if self.last_error:
            return self.last_error
        if self.lab_only_import:
            return "Import-only lab connector. No execution or remote sync is supported."
        if not (self.config or {}).get("endpoint_url"):
            return "Set an endpoint URL and credentials before manual sync."
        return "Ready for manual sync."

    @property
    def consecutive_failures(self) -> int:
        failures = 0
        for run in sorted(self.runs, key=lambda item: item.started_at, reverse=True):
            if run.status == "failed":
                failures += 1
                continue
            if run.status == "completed":
                break
        return failures

    @property
    def last_successful_sync_at(self) -> datetime | None:
        completed_runs = [run.completed_at for run in self.runs if run.status == "completed" and run.completed_at]
        return max(completed_runs) if completed_runs else None

    @property
    def sanitized_config(self) -> dict:
        config = {
            "endpoint_url": (self.config or {}).get("endpoint_url"),
            "auth_type": (self.config or {}).get("auth_type", "none"),
            "username": (self.config or {}).get("username"),
            "verify_tls": bool((self.config or {}).get("verify_tls", True)),
            "timeout_seconds": int((self.config or {}).get("timeout_seconds", 15)),
            "lookback_minutes": int((self.config or {}).get("lookback_minutes", 60)),
            "request_headers": {},
            "query_params": dict((self.config or {}).get("query_params", {})),
            "has_password": bool((self.config or {}).get("password")),
            "has_api_token": bool((self.config or {}).get("api_token")),
            "configured": bool((self.config or {}).get("endpoint_url")) if self.supports_manual_sync else True,
            "supports_manual_sync": self.supports_manual_sync,
            "supports_file_import": self.supports_file_import,
            "lab_only_import": self.lab_only_import,
            "supported_formats": self.supported_formats,
        }
        for key, value in dict((self.config or {}).get("request_headers", {})).items():
            lowered = key.lower()
            config["request_headers"][key] = "***" if any(token in lowered for token in {"auth", "token", "secret", "key"}) else value
        return config


class IntegrationRun(Base):
    __tablename__ = "integration_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=make_id)
    integration_id: Mapped[str] = mapped_column(ForeignKey("integrations.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(50))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    records_ingested: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    integration: Mapped["Integration"] = relationship(back_populates="runs")

    @property
    def mode(self) -> str | None:
        return self.summary.get("mode") if isinstance(self.summary, dict) else None

    @property
    def input_format(self) -> str | None:
        return self.summary.get("input_format") if isinstance(self.summary, dict) else None

    @property
    def alerts_created(self) -> int:
        return int(self.summary.get("alerts_created", 0)) if isinstance(self.summary, dict) else 0

    @property
    def alerts_updated(self) -> int:
        return int(self.summary.get("alerts_updated", 0)) if isinstance(self.summary, dict) else 0

    @property
    def logs_created(self) -> int:
        return int(self.summary.get("logs_created", 0)) if isinstance(self.summary, dict) else 0

    @property
    def assets_touched(self) -> int:
        return int(self.summary.get("assets_touched", 0)) if isinstance(self.summary, dict) else 0

    @property
    def incident_candidates(self) -> int:
        return int(self.summary.get("incident_candidates", 0)) if isinstance(self.summary, dict) else 0

    @property
    def normalized_records(self) -> int:
        return int(self.summary.get("normalized_records", self.records_ingested)) if isinstance(self.summary, dict) else self.records_ingested

    @property
    def imported_lab_data(self) -> bool:
        return bool(self.summary.get("imported_lab_data", False)) if isinstance(self.summary, dict) else False


class Alert(TimestampMixin, Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=make_id)
    external_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(50), index=True)
    source_type: Mapped[str] = mapped_column(String(50), default="telemetry", index=True)
    event_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    severity: Mapped[AlertSeverity] = mapped_column(String(20), index=True)
    status: Mapped[AlertStatus] = mapped_column(String(20), default=AlertStatus.OPEN, index=True)
    risk_score: Mapped[float] = mapped_column(Float, default=0)
    risk_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    explainability: Mapped[list] = mapped_column(JSON, default=list)
    explanation_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations: Mapped[list] = mapped_column(JSON, default=list)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    asset_id: Mapped[str | None] = mapped_column(ForeignKey("assets.id", ondelete="SET NULL"), nullable=True, index=True)
    integration_id: Mapped[str | None] = mapped_column(
        ForeignKey("integrations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    assigned_to_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    parsed_payload: Mapped[dict] = mapped_column(JSON, default=dict)

    asset: Mapped[Asset | None] = relationship(back_populates="alerts")
    integration: Mapped[Integration | None] = relationship(back_populates="alerts")
    assignee: Mapped[User | None] = relationship(back_populates="assigned_alerts", foreign_keys=[assigned_to_id])
    comments: Mapped[list["AlertComment"]] = relationship(back_populates="alert", cascade="all, delete-orphan")
    incident_links: Mapped[list["IncidentAlertLink"]] = relationship(
        back_populates="alert", cascade="all, delete-orphan"
    )
    response_recommendations: Mapped[list["ResponseRecommendation"]] = relationship(
        back_populates="alert", cascade="all, delete-orphan"
    )

    @property
    def incident_ids(self) -> list[str]:
        return [link.incident_id for link in self.incident_links]


class ResponseRecommendation(Base):
    __tablename__ = "response_recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=make_id)
    alert_id: Mapped[str] = mapped_column(ForeignKey("alerts.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    alert: Mapped[Alert] = relationship(back_populates="response_recommendations")


class AlertComment(Base):
    __tablename__ = "alert_comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=make_id)
    alert_id: Mapped[str] = mapped_column(ForeignKey("alerts.id", ondelete="CASCADE"), index=True)
    author_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    alert: Mapped[Alert] = relationship(back_populates="comments")
    author: Mapped[User | None] = relationship()


class Incident(TimestampMixin, Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=make_id)
    reference: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[IncidentStatus] = mapped_column(String(20), default=IncidentStatus.OPEN, index=True)
    priority: Mapped[IncidentPriority] = mapped_column(String(10), default=IncidentPriority.P3, index=True)
    assignee_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[list] = mapped_column(JSON, default=list)

    assignee: Mapped[User | None] = relationship(back_populates="assigned_incidents", foreign_keys=[assignee_id])
    created_by: Mapped[User | None] = relationship(foreign_keys=[created_by_id])
    events: Mapped[list["IncidentEvent"]] = relationship(back_populates="incident", cascade="all, delete-orphan")
    alert_links: Mapped[list["IncidentAlertLink"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )

    @property
    def linked_alerts(self) -> list["Alert"]:
        return [link.alert for link in self.alert_links]


class IncidentEvent(Base):
    __tablename__ = "incident_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=make_id)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), index=True)
    author_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), default="note", index=True)
    body: Mapped[str] = mapped_column(Text)
    event_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    is_timeline_event: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    incident: Mapped[Incident] = relationship(back_populates="events")
    author: Mapped[User | None] = relationship()


class IncidentAlertLink(Base):
    __tablename__ = "incident_alert_links"
    __table_args__ = (UniqueConstraint("incident_id", "alert_id", name="uq_incident_alert_link"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=make_id)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), index=True)
    alert_id: Mapped[str] = mapped_column(ForeignKey("alerts.id", ondelete="CASCADE"), index=True)

    incident: Mapped[Incident] = relationship(back_populates="alert_links")
    alert: Mapped[Alert] = relationship(back_populates="incident_links")


class LogEntry(Base):
    __tablename__ = "log_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=make_id)
    source: Mapped[str] = mapped_column(String(50), index=True)
    level: Mapped[str] = mapped_column(String(50))
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    message: Mapped[str] = mapped_column(Text)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    asset_id: Mapped[str | None] = mapped_column(ForeignKey("assets.id", ondelete="SET NULL"), nullable=True, index=True)
    integration_id: Mapped[str | None] = mapped_column(
        ForeignKey("integrations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    parsed_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    fingerprint: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    asset: Mapped[Asset | None] = relationship(back_populates="logs")
    integration: Mapped[Integration | None] = relationship(back_populates="logs")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=make_id)
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(255), index=True)
    entity_type: Mapped[str] = mapped_column(String(100), index=True)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    actor: Mapped[User | None] = relationship()


class RiskModelMetadata(Base):
    __tablename__ = "risk_model_metadata"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=make_id)
    model_name: Mapped[str] = mapped_column(String(100))
    version: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    feature_names: Mapped[list] = mapped_column(JSON, default=list)
    training_parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    @property
    def feature_version(self) -> str | None:
        if isinstance(self.training_parameters, dict):
            value = self.training_parameters.get("feature_version")
            return str(value) if value else None
        return None

    @property
    def performance_notes(self) -> list[str]:
        if isinstance(self.training_parameters, dict):
            value = self.training_parameters.get("performance_notes", [])
            if isinstance(value, list):
                return [str(item) for item in value]
        return [self.notes] if self.notes else []


class JobRecord(Base):
    __tablename__ = "job_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=make_id)
    job_type: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[JobStatus] = mapped_column(String(20), default=JobStatus.QUEUED, index=True)
    requested_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    requested_by: Mapped[User | None] = relationship()


# Compatibility aliases used by the existing service and test code.
IncidentNote = IncidentEvent
ModelMetadata = RiskModelMetadata
