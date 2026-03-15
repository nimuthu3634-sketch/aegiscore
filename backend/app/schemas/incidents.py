from datetime import datetime

from pydantic import BaseModel

from app.core.enums import AlertSeverity, IncidentStatus, IntegrationTool, UserRole
from app.schemas.base import ORMModel


class IncidentAssigneeOption(BaseModel):
    id: str
    full_name: str
    email: str
    role: UserRole


class IncidentRead(ORMModel):
    id: str
    alert_id: str | None
    alert_title: str | None
    title: str
    priority: AlertSeverity
    status: IncidentStatus
    notes: str
    opened_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    assigned_to_user_id: str | None
    assigned_to_name: str | None
    affected_asset: str
    source_tool: IntegrationTool | None
    summary: str


class IncidentListResponse(BaseModel):
    items: list[IncidentRead]
    available_assignees: list[IncidentAssigneeOption]
    total_items: int


class IncidentCreateRequest(BaseModel):
    alert_id: str
    assigned_to_user_id: str | None = None
    priority: AlertSeverity | None = None
    notes: str = ""


class IncidentUpdateRequest(BaseModel):
    assigned_to_user_id: str | None = None
    priority: AlertSeverity | None = None
    status: IncidentStatus | None = None
    notes: str | None = None
