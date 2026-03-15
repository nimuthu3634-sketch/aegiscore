from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.core.enums import IntegrationHealth, IntegrationTool, VirtualMachineStatus
from app.schemas.base import ORMModel


class IntegrationRead(ORMModel):
    id: str
    tool_name: IntegrationTool
    status: IntegrationHealth
    last_sync_at: datetime
    notes: str
    imported_alert_count: int = 0
    imported_log_count: int = 0
    last_import_at: datetime | None = None
    last_import_message: str | None = None


class DemoImportResponse(BaseModel):
    imported_alert_count: int
    imported_log_count: int
    skipped_count: int
    last_import_at: datetime
    message: str


class DemoIntegrationStatusResponse(IntegrationRead):
    available_demo_payloads: int
    latest_imported_alert_titles: list[str]


class WazuhImportRequest(BaseModel):
    alerts: list[dict[str, Any]]


class WazuhImportResponse(DemoImportResponse):
    pass


class WazuhStatusResponse(DemoIntegrationStatusResponse):
    pass


class SuricataImportRequest(BaseModel):
    events: list[dict[str, Any]]


class SuricataImportResponse(DemoImportResponse):
    pass


class SuricataStatusResponse(DemoIntegrationStatusResponse):
    pass


class NmapPortResult(BaseModel):
    port: int
    service_name: str | None = None
    protocol: str = "tcp"
    state: str = "open"


class NmapImportItem(BaseModel):
    host: str
    open_ports: list[NmapPortResult]
    service_names: list[str] = []
    scan_timestamp: str | int | float | datetime | None = None
    scan_notes: str | None = None


class NmapImportRequest(BaseModel):
    results: list[NmapImportItem]


class NmapImportResponse(DemoImportResponse):
    pass


class NmapStatusResponse(DemoIntegrationStatusResponse):
    pass


class HydraImportItem(BaseModel):
    target_system: str
    protocol: str
    result_summary: str
    timestamp: str | int | float | datetime | None = None
    notes: str | None = None


class HydraImportRequest(BaseModel):
    results: list[HydraImportItem]


class HydraImportResponse(DemoImportResponse):
    pass


class HydraStatusResponse(DemoIntegrationStatusResponse):
    pass


class VirtualMachineRead(ORMModel):
    id: str
    vm_name: str
    role: str
    os_type: str
    ip_address: str
    status: VirtualMachineStatus
    notes: str


class VirtualMachineCreateRequest(BaseModel):
    vm_name: str
    role: str
    os_type: str
    ip_address: str
    status: VirtualMachineStatus = VirtualMachineStatus.PROVISIONING
    notes: str = ""


class VirtualMachineUpdateRequest(BaseModel):
    vm_name: str | None = None
    role: str | None = None
    os_type: str | None = None
    ip_address: str | None = None
    status: VirtualMachineStatus | None = None
    notes: str | None = None


class WazuhSampleAlertRead(BaseModel):
    timestamp: str
    agent: dict[str, Any]
    rule: dict[str, Any]
    full_log: str
    id: str | None = None
