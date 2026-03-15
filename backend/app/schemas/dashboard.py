from pydantic import BaseModel


class DashboardMetric(BaseModel):
    label: str
    value: str
    note: str


class DashboardSummary(BaseModel):
    metrics: list[DashboardMetric]
    recent_alert_count: int
    recent_incident_count: int
