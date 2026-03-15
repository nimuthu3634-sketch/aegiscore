from app.core.enums import AlertSeverity, IncidentStatus
from app.schemas.base import ORMModel


class IncidentRead(ORMModel):
    id: str
    title: str
    description: str
    owner_name: str
    status: IncidentStatus
    priority: AlertSeverity
