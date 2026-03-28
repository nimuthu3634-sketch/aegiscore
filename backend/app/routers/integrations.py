from fastapi import APIRouter, Depends, status

from app.core.enums import UserRole
from app.schemas.integrations import (
    HydraImportRequest,
    HydraImportResponse,
    HydraStatusResponse,
    IntegrationRead,
    NmapImportRequest,
    NmapImportResponse,
    NmapStatusResponse,
    SuricataImportRequest,
    SuricataImportResponse,
    SuricataStatusResponse,
    WazuhImportRequest,
    WazuhImportResponse,
    WazuhStatusResponse,
)
from app.services.hydra_integration import get_hydra_status, import_hydra_results
from app.services.integrations import list_integrations
from app.services.nmap_integration import get_nmap_status, import_nmap_results
from app.services.suricata_integration import get_suricata_status, import_suricata_events
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


@router.get("/suricata/status", response_model=SuricataStatusResponse)
def get_suricata_integration_status(
    current_user: dict = Depends(get_current_active_user),
) -> SuricataStatusResponse:
    return SuricataStatusResponse.model_validate(get_suricata_status())


@router.post(
    "/suricata/import",
    response_model=SuricataImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_suricata_demo_data(
    payload: SuricataImportRequest,
    current_user: dict = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
) -> SuricataImportResponse:
    result = import_suricata_events(payload.events)
    return SuricataImportResponse.model_validate(result)


@router.get("/nmap/status", response_model=NmapStatusResponse)
def get_nmap_integration_status(
    current_user: dict = Depends(get_current_active_user),
) -> NmapStatusResponse:
    return NmapStatusResponse.model_validate(get_nmap_status())


@router.post("/nmap/import", response_model=NmapImportResponse, status_code=status.HTTP_201_CREATED)
def import_nmap_demo_data(
    payload: NmapImportRequest,
    current_user: dict = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
) -> NmapImportResponse:
    result = import_nmap_results([item.model_dump() for item in payload.results])
    return NmapImportResponse.model_validate(result)


@router.get("/hydra/status", response_model=HydraStatusResponse)
def get_hydra_integration_status(
    current_user: dict = Depends(get_current_active_user),
) -> HydraStatusResponse:
    return HydraStatusResponse.model_validate(get_hydra_status())


@router.post("/hydra/import", response_model=HydraImportResponse, status_code=status.HTTP_201_CREATED)
def import_hydra_demo_data(
    payload: HydraImportRequest,
    current_user: dict = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
) -> HydraImportResponse:
    result = import_hydra_results([item.model_dump() for item in payload.results])
    return HydraImportResponse.model_validate(result)
