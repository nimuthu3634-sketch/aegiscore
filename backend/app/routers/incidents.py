from fastapi import APIRouter, Depends

from app.core.enums import AlertSeverity, IncidentStatus, UserRole
from app.schemas.incidents import (
    IncidentCreateRequest,
    IncidentListResponse,
    IncidentRead,
    IncidentUpdateRequest,
)
from app.services.incidents import create_incident, get_incident_by_id, list_incidents, update_incident
from app.utils.auth import get_current_active_user, require_roles

router = APIRouter()


@router.get("", response_model=IncidentListResponse)
def get_incidents(
    priority: AlertSeverity | None = None,
    status: IncidentStatus | None = None,
    assignee_id: str | None = None,
    current_user: dict = Depends(get_current_active_user),
) -> IncidentListResponse:
    result = list_incidents(priority=priority, status_filter=status, assignee_id=assignee_id)
    return IncidentListResponse.model_validate(
        {
            **result,
            "items": [IncidentRead.model_validate(incident) for incident in result["items"]],
        }
    )


@router.get("/{id}", response_model=IncidentRead)
def get_incident(id: str, current_user: dict = Depends(get_current_active_user)) -> IncidentRead:
    return IncidentRead.model_validate(get_incident_by_id(id))


@router.post("", response_model=IncidentRead)
def create_new_incident(
    payload: IncidentCreateRequest,
    current_user: dict = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
) -> IncidentRead:
    return IncidentRead.model_validate(
        create_incident(
            alert_id=payload.alert_id,
            assigned_to_user_id=payload.assigned_to_user_id,
            priority=payload.priority,
            notes=payload.notes,
        )
    )


@router.patch("/{id}", response_model=IncidentRead)
def patch_incident(
    id: str,
    payload: IncidentUpdateRequest,
    current_user: dict = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
) -> IncidentRead:
    return IncidentRead.model_validate(update_incident(id, payload.model_dump(exclude_unset=True)))
