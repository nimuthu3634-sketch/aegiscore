from datetime import datetime

from app.core.enums import IntegrationType
from app.schemas.base import ORMModel


class IntegrationRead(ORMModel):
    id: str
    name: str
    integration_type: IntegrationType
    is_enabled: bool
    last_sync_at: datetime
