from datetime import datetime

from pydantic import BaseModel

from app.core.enums import AlertSeverity, IncidentStatus


class DashboardSummary(BaseModel):
    total_alerts: int
    critical_alerts: int
    open_incidents: int
    resolved_incidents: int


class AlertsOverTimePoint(BaseModel):
    label: str
    total: int


class AlertsBySeverityPoint(BaseModel):
    severity: AlertSeverity
    count: int


class AlertsBySourceToolPoint(BaseModel):
    source_tool: str
    count: int


class DashboardCharts(BaseModel):
    alerts_over_time: list[AlertsOverTimePoint]
    alerts_by_severity: list[AlertsBySeverityPoint]
    alerts_by_source_tool: list[AlertsBySourceToolPoint]


class DashboardRecentIncident(BaseModel):
    id: str
    title: str
    priority: AlertSeverity
    status: IncidentStatus
    analyst_name: str | None
    affected_asset: str
    summary: str
    updated_at: datetime
