from datetime import date, datetime
from typing import Any

from pydantic import BaseModel

from app.core.enums import AlertSeverity, IncidentStatus, IntegrationTool, ReportStatus, ReportType
from app.schemas.alerts import AlertRead
from app.schemas.base import ORMModel


class ReportRead(ORMModel):
    id: str
    title: str
    report_type: ReportType
    generated_by_user_id: str | None
    generated_by_name: str | None = None
    content_json: dict[str, Any]
    status: ReportStatus
    created_at: datetime


class ReportSeverityPoint(BaseModel):
    severity: AlertSeverity
    count: int


class ReportSourceToolPoint(BaseModel):
    source_tool: IntegrationTool
    count: int


class ReportIncidentStatusPoint(BaseModel):
    status: IncidentStatus
    count: int


class ReportAnomalySummary(BaseModel):
    model_name: str
    trained_on_events: int
    feature_labels: list[str]
    trained_at: datetime
    average_anomaly_score: float
    anomalous_alert_count: int
    high_anomaly_alert_count: int
    top_anomalous_alerts: list[AlertRead]


class ReportSummary(BaseModel):
    date_from: date | None
    date_to: date | None
    reports_generated: int
    draft_reports: int
    ready_reports: int
    filtered_alert_count: int
    filtered_incident_count: int
    alerts_by_severity: list[ReportSeverityPoint]
    alerts_by_source_tool: list[ReportSourceToolPoint]
    incidents_by_status: list[ReportIncidentStatusPoint]
    anomaly_summary: ReportAnomalySummary


class ReportGenerateRequest(BaseModel):
    title: str | None = None
    report_type: ReportType = ReportType.OPERATIONS
    date_from: date | None = None
    date_to: date | None = None
