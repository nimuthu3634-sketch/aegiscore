from datetime import datetime

from pydantic import BaseModel

from app.core.enums import AlertSeverity, AlertStatus, IntegrationTool
from app.schemas.base import ORMModel


class AlertRead(ORMModel):
    id: str
    title: str
    description: str
    source: str
    source_tool: IntegrationTool
    severity: AlertSeverity
    status: AlertStatus
    confidence_score: float
    anomaly_score: float
    is_anomalous: bool
    anomaly_explanation: str
    created_at: datetime


class AlertListResponse(BaseModel):
    items: list[AlertRead]
    page: int
    page_size: int
    total_items: int
    total_pages: int


class AlertStatusUpdateRequest(BaseModel):
    status: AlertStatus
