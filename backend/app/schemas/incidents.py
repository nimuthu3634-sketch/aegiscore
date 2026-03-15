from datetime import datetime

from app.core.enums import AlertSeverity, IncidentStatus
from app.schemas.base import ORMModel


class IncidentRead(ORMModel):
    id: str
    alert_id: str | None
    assigned_to_user_id: str | None
    priority: AlertSeverity
    status: IncidentStatus
    notes: str
    opened_at: datetime
    closed_at: datetime | None
