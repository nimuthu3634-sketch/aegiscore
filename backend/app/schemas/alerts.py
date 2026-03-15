from datetime import datetime

from app.core.enums import AlertSeverity, AlertStatus
from app.schemas.base import ORMModel


class AlertRead(ORMModel):
    id: str
    title: str
    source: str
    severity: AlertSeverity
    status: AlertStatus
    summary: str
    occurred_at: datetime
