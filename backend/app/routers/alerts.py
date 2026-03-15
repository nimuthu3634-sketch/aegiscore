from fastapi import APIRouter, Depends, Query

from app.core.enums import AlertSeverity, AlertStatus, IntegrationTool, UserRole
from app.schemas.alerts import AlertListResponse, AlertRead, AlertStatusUpdateRequest
from app.services.alerts import get_alert_by_id, list_alerts, update_alert_status
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
