from datetime import datetime

from app.core.enums import AlertSeverity, AlertStatus
from app.schemas.base import ORMModel


class AlertRead(ORMModel):
    id: str
    title: str
    description: str
    source: str
    source_tool: str
    severity: AlertSeverity
    status: AlertStatus
    confidence_score: float
    created_at: datetime
