from fastapi import APIRouter, Depends, Query, status

from app.core.enums import AlertSeverity, AlertStatus, IntegrationTool, UserRole
from app.schemas.alerts import AlertListResponse, AlertRead, AlertStatusUpdateRequest
from app.schemas.response_actions import (
    AlertResponseActionsResponse,
    ResponseActionExecuteRequest,
    ResponseActionRead,
)
from app.services.alerts import get_alert_by_id, list_alerts, update_alert_status
from app.services.response_actions import execute_response_action, list_response_actions
from app.utils.auth import get_current_active_user, require_roles

router = APIRouter()


@router.get("", response_model=AlertListResponse)
def get_alerts(
    severity: AlertSeverity | None = None,
    status: AlertStatus | None = None,
    source_tool: IntegrationTool | None = None,
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=8, ge=1, le=25),
    current_user: dict = Depends(get_current_active_user),
) -> AlertListResponse:
    result = list_alerts(
        severity=severity,
        status_filter=status,
        source_tool=source_tool,
        search=search,
        page=page,
        page_size=page_size,
    )
    return AlertListResponse.model_validate(
        {
            **result,
            "items": [AlertRead.model_validate(alert) for alert in result["items"]],
        }
    )


@router.patch("/{id}/status", response_model=AlertRead)
def patch_alert_status(
    id: str,
    payload: AlertStatusUpdateRequest,
    current_user: dict = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
) -> AlertRead:
    return AlertRead.model_validate(update_alert_status(id, payload.status))


@router.get("/{id}", response_model=AlertRead)
def get_alert(id: str, current_user: dict = Depends(get_current_active_user)) -> AlertRead:
    return AlertRead.model_validate(get_alert_by_id(id))


@router.get("/{id}/response-actions", response_model=AlertResponseActionsResponse)
def get_alert_response_actions(
    id: str,
    current_user: dict = Depends(get_current_active_user),
) -> AlertResponseActionsResponse:
    result = list_response_actions(id)
    return AlertResponseActionsResponse.model_validate(
        {
            **result,
            "items": [ResponseActionRead.model_validate(action) for action in result["items"]],
        }
    )


@router.post(
    "/{id}/response-actions",
    response_model=ResponseActionRead,
    status_code=status.HTTP_201_CREATED,
)
def execute_alert_response_action(
    id: str,
    payload: ResponseActionExecuteRequest,
    current_user: dict = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
) -> ResponseActionRead:
    action = execute_response_action(
        alert_id=id,
        action_type=payload.action_type,
        notes=payload.notes,
        actor=current_user,
    )
    return ResponseActionRead.model_validate(action)
