from datetime import datetime

from app.core.enums import IntegrationHealth, IntegrationTool
from app.schemas.base import ORMModel


class IntegrationRead(ORMModel):
    id: str
    tool_name: IntegrationTool
    status: IntegrationHealth
    last_sync_at: datetime
    notes: str
