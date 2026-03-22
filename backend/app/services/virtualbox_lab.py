from sqlalchemy import select

from fastapi import HTTPException, status

from app.core.enums import IntegrationHealth, IntegrationTool, VirtualMachineStatus
from app.models.virtual_machine import VirtualMachine
from app.services.integrations import get_integration_by_tool, update_integration_runtime
from app.services.mock_store import DEMO_VIRTUAL_MACHINES
from app.services.persistence import run_with_optional_db
from app.services.record_ids import next_prefixed_id
from app.utils.time import utc_now


def _virtual_machine_from_model(virtual_machine: VirtualMachine) -> dict:
    return {
        "id": virtual_machine.id,
        "vm_name": virtual_machine.vm_name,
        "role": virtual_machine.role,
        "os_type": virtual_machine.os_type,
        "ip_address": virtual_machine.ip_address,
        "status": virtual_machine.status,
        "notes": virtual_machine.notes,
    }


def _load_persisted_virtual_machines() -> list[dict]:
    def operation(db) -> list[dict]:
        virtual_machines = db.scalars(select(VirtualMachine)).all()
        return [
            _virtual_machine_from_model(virtual_machine)
            for virtual_machine in virtual_machines
        ]

    return run_with_optional_db(operation, lambda: [])


def load_virtual_machine_records() -> list[dict]:
    merged_virtual_machines = {
        virtual_machine["id"]: dict(virtual_machine)
        for virtual_machine in DEMO_VIRTUAL_MACHINES
    }

    for persisted_virtual_machine in _load_persisted_virtual_machines():
        if persisted_virtual_machine["id"] in merged_virtual_machines:
            merged_virtual_machines[persisted_virtual_machine["id"]] = {
                **merged_virtual_machines[persisted_virtual_machine["id"]],
                **persisted_virtual_machine,
            }
        else:
            merged_virtual_machines[persisted_virtual_machine["id"]] = persisted_virtual_machine

    return list(merged_virtual_machines.values())


def _persist_virtual_machine_record(vm_record: dict) -> None:
    def operation(db) -> None:
        db.merge(
            VirtualMachine(
                id=vm_record["id"],
                vm_name=vm_record["vm_name"],
                role=vm_record["role"],
                os_type=vm_record["os_type"],
                ip_address=vm_record["ip_address"],
                status=vm_record["status"],
                notes=vm_record.get("notes", ""),
            )
        )
        db.commit()

    run_with_optional_db(operation, lambda: None)


def _sorted_virtual_machines() -> list[dict]:
    status_order = {
        VirtualMachineStatus.RUNNING: 0,
        VirtualMachineStatus.PROVISIONING: 1,
        VirtualMachineStatus.PAUSED: 2,
        VirtualMachineStatus.STOPPED: 3,
    }
    return sorted(
        load_virtual_machine_records(),
        key=lambda item: (status_order.get(item["status"], 99), item["role"], item["vm_name"]),
    )


def _sync_virtualbox_integration(last_message: str | None = None) -> None:
    integration = get_integration_by_tool(IntegrationTool.VIRTUALBOX)
    virtual_machines = load_virtual_machine_records()
    status_values = [item["status"] for item in virtual_machines]

    if status_values and all(item == VirtualMachineStatus.RUNNING for item in status_values):
        integration_status = IntegrationHealth.CONNECTED
    elif status_values and any(item == VirtualMachineStatus.RUNNING for item in status_values):
        integration_status = IntegrationHealth.DEGRADED
    elif status_values:
        integration_status = IntegrationHealth.PENDING
    else:
        integration_status = IntegrationHealth.OFFLINE

    sync_time = utc_now()
    update_integration_runtime(
        IntegrationTool.VIRTUALBOX,
        status=integration_status,
        last_sync_at=sync_time,
        notes="VirtualBox inventory tracking and environment readiness monitoring.",
        last_import_at=sync_time if last_message else integration.get("last_import_at"),
        last_import_message=last_message or integration.get("last_import_message"),
    )


def list_virtual_machines() -> list[dict]:
    _sync_virtualbox_integration()
    return _sorted_virtual_machines()


def get_virtual_machine_by_id(vm_id: str) -> dict:
    vm_record = next((item for item in load_virtual_machine_records() if item["id"] == vm_id), None)
    if not vm_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Virtual machine not found.")

    return vm_record


def create_virtual_machine(payload: dict) -> dict:
    vm_record = {
        "id": next_prefixed_id("vm", (item["id"] for item in load_virtual_machine_records())),
        "vm_name": payload["vm_name"].strip(),
        "role": payload["role"].strip(),
        "os_type": payload["os_type"].strip(),
        "ip_address": payload["ip_address"].strip(),
        "status": payload.get("status", VirtualMachineStatus.PROVISIONING),
        "notes": payload.get("notes", "").strip(),
    }
    DEMO_VIRTUAL_MACHINES.append(vm_record)
    _persist_virtual_machine_record(vm_record)
    _sync_virtualbox_integration(
        f"Inventory updated. {len(load_virtual_machine_records())} VirtualBox VMs are now tracked."
    )
    return vm_record


def update_virtual_machine(vm_id: str, payload: dict) -> dict:
    vm_record = get_virtual_machine_by_id(vm_id)
    memory_virtual_machine = next((item for item in DEMO_VIRTUAL_MACHINES if item["id"] == vm_id), None)
    target_virtual_machine = memory_virtual_machine if memory_virtual_machine is not None else vm_record

    for field in ("vm_name", "role", "os_type", "ip_address", "status", "notes"):
        if payload.get(field) is not None:
            value = payload[field]
            updated_value = value.strip() if isinstance(value, str) else value
            target_virtual_machine[field] = updated_value
            vm_record[field] = updated_value

    _persist_virtual_machine_record(vm_record)
    _sync_virtualbox_integration(f"VirtualBox VM {vm_record['vm_name']} was updated in the inventory.")
    return get_virtual_machine_by_id(vm_id)
