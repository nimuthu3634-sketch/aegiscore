from fastapi import HTTPException, status

from app.core.enums import IntegrationHealth, IntegrationTool, VirtualMachineStatus
from app.services.integrations import get_integration_by_tool
from app.services.mock_store import DEMO_VIRTUAL_MACHINES
from app.utils.time import utc_now


def _sorted_virtual_machines() -> list[dict]:
    status_order = {
        VirtualMachineStatus.RUNNING: 0,
        VirtualMachineStatus.PROVISIONING: 1,
        VirtualMachineStatus.PAUSED: 2,
        VirtualMachineStatus.STOPPED: 3,
    }
    return sorted(
        DEMO_VIRTUAL_MACHINES,
        key=lambda item: (status_order.get(item["status"], 99), item["role"], item["vm_name"]),
    )


def _sync_virtualbox_integration(last_message: str | None = None) -> None:
    integration = get_integration_by_tool(IntegrationTool.VIRTUALBOX)
    status_values = [item["status"] for item in DEMO_VIRTUAL_MACHINES]

    if status_values and all(item == VirtualMachineStatus.RUNNING for item in status_values):
        integration["status"] = IntegrationHealth.CONNECTED
    elif status_values and any(item == VirtualMachineStatus.RUNNING for item in status_values):
        integration["status"] = IntegrationHealth.DEGRADED
    elif status_values:
        integration["status"] = IntegrationHealth.PENDING
    else:
        integration["status"] = IntegrationHealth.OFFLINE

    sync_time = utc_now()
    integration["last_sync_at"] = sync_time
    integration["notes"] = "VirtualBox inventory tracking and environment readiness monitoring."

    if last_message:
        integration["last_import_at"] = sync_time
        integration["last_import_message"] = last_message


def list_virtual_machines() -> list[dict]:
    _sync_virtualbox_integration()
    return _sorted_virtual_machines()


def get_virtual_machine_by_id(vm_id: str) -> dict:
    vm_record = next((item for item in DEMO_VIRTUAL_MACHINES if item["id"] == vm_id), None)
    if not vm_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Virtual machine not found.")

    return vm_record


def create_virtual_machine(payload: dict) -> dict:
    vm_record = {
        "id": f"vm-{len(DEMO_VIRTUAL_MACHINES) + 1:03d}",
        "vm_name": payload["vm_name"].strip(),
        "role": payload["role"].strip(),
        "os_type": payload["os_type"].strip(),
        "ip_address": payload["ip_address"].strip(),
        "status": payload.get("status", VirtualMachineStatus.PROVISIONING),
        "notes": payload.get("notes", "").strip(),
    }
    DEMO_VIRTUAL_MACHINES.append(vm_record)
    _sync_virtualbox_integration(
        f"Inventory updated. {len(DEMO_VIRTUAL_MACHINES)} VirtualBox VMs are now tracked."
    )
    return vm_record


def update_virtual_machine(vm_id: str, payload: dict) -> dict:
    vm_record = get_virtual_machine_by_id(vm_id)

    for field in ("vm_name", "role", "os_type", "ip_address", "status", "notes"):
        if payload.get(field) is not None:
            value = payload[field]
            vm_record[field] = value.strip() if isinstance(value, str) else value

    _sync_virtualbox_integration(f"VirtualBox VM {vm_record['vm_name']} was updated in the inventory.")
    return vm_record
