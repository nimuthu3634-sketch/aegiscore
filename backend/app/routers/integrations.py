from fastapi import APIRouter, Depends, status

from app.core.enums import UserRole
from app.schemas.integrations import (
    IntegrationRead,
    WazuhImportRequest,
    WazuhImportResponse,
    WazuhStatusResponse,
)
from app.services.integrations import list_integrations
from app.services.wazuh_integration import get_wazuh_status, import_wazuh_alerts
from app.utils.auth import get_current_active_user, require_roles

router = APIRouter()


@router.get("/status", response_model=list[IntegrationRead])
def get_integrations_status(
    current_user: dict = Depends(get_current_active_user),
) -> list[IntegrationRead]:
    return [IntegrationRead.model_validate(item) for item in list_integrations()]


@router.get("/wazuh/status", response_model=WazuhStatusResponse)
def get_wazuh_integration_status(
    current_user: dict = Depends(get_current_active_user),
) -> WazuhStatusResponse:
    return WazuhStatusResponse.model_validate(get_wazuh_status())


@router.post("/wazuh/import", response_model=WazuhImportResponse, status_code=status.HTTP_201_CREATED)
def import_wazuh_demo_data(
    payload: WazuhImportRequest,
    current_user: dict = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
) -> WazuhImportResponse:
    result = import_wazuh_alerts(payload.alerts)
    return WazuhImportResponse.model_validate(result)
