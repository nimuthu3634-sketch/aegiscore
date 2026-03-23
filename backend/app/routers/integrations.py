from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.core.enums import UserRole
from app.schemas.integrations import (
    HydraImportRequest,
    HydraImportResponse,
    HydraStatusResponse,
    IntegrationRead,
    LanlImportResponse,
    LanlStatusResponse,
    NmapImportRequest,
    NmapImportResponse,
    NmapStatusResponse,
    SuricataImportRequest,
    SuricataImportResponse,
    SuricataStatusResponse,
    VirtualMachineCreateRequest,
    VirtualMachineRead,
    VirtualMachineUpdateRequest,
    WazuhImportRequest,
    WazuhImportResponse,
    WazuhStatusResponse,
)
from app.services.hydra_integration import get_hydra_status, import_hydra_results
from app.services.integrations import list_integrations
from app.services.lanl_integration import get_lanl_status, import_lanl_dataset_file
from app.services.nmap_integration import get_nmap_status, import_nmap_results
from app.services.suricata_integration import get_suricata_status, import_suricata_events
from app.services.virtualbox_lab import create_virtual_machine, list_virtual_machines, update_virtual_machine
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


@router.get("/lanl/status", response_model=LanlStatusResponse)
def get_lanl_integration_status(
    current_user: dict = Depends(get_current_active_user),
) -> LanlStatusResponse:
    return LanlStatusResponse.model_validate(get_lanl_status())


@router.post("/lanl/import", response_model=LanlImportResponse, status_code=status.HTTP_201_CREATED)
def import_lanl_dataset(
    dataset_type: str = Form(...),
    dataset_file: UploadFile = File(...),
    redteam_file: UploadFile | None = File(default=None),
    max_records: int = Form(default=1000),
    current_user: dict = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
) -> LanlImportResponse:
    result = import_lanl_dataset_file(
        dataset_type,
        dataset_file,
        redteam_file=redteam_file,
        max_records=max_records,
    )
    return LanlImportResponse.model_validate(result)


@router.get("/virtualbox/lab", response_model=list[VirtualMachineRead])
def get_virtualbox_lab_environment(
    current_user: dict = Depends(get_current_active_user),
) -> list[VirtualMachineRead]:
    return [VirtualMachineRead.model_validate(item) for item in list_virtual_machines()]


@router.post("/virtualbox/lab", response_model=VirtualMachineRead, status_code=status.HTTP_201_CREATED)
def create_virtualbox_lab_asset(
    payload: VirtualMachineCreateRequest,
    current_user: dict = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
) -> VirtualMachineRead:
    return VirtualMachineRead.model_validate(create_virtual_machine(payload.model_dump()))


@router.patch("/virtualbox/lab/{id}", response_model=VirtualMachineRead)
def update_virtualbox_lab_asset(
    id: str,
    payload: VirtualMachineUpdateRequest,
    current_user: dict = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
) -> VirtualMachineRead:
    return VirtualMachineRead.model_validate(update_virtual_machine(id, payload.model_dump()))
