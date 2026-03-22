from copy import deepcopy

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.core.enums import (
    AlertSeverity,
    IntegrationHealth,
    IntegrationTool,
    ResponseActionType,
    VirtualMachineStatus,
)
from app.db.base import Base
from app.services.anomaly import get_anomaly_summary
from app.services import alerts as alerts_service
from app.services import auth as auth_service
from app.services import integrations as integrations_service
from app.services import incidents as incidents_service
from app.services import logs as logs_service
from app.services import response_actions as response_actions_service
from app.services import users as users_service
from app.services import virtualbox_lab as virtualbox_lab_service
from app.services.dashboard import get_dashboard_summary
from app.services.hydra_integration import import_hydra_results
from app.services.websocket import build_alert_stream_ready_payload
from app.services.mock_store import (
    DEMO_ALERTS,
    DEMO_BLOCKED_IPS,
    DEMO_INCIDENTS,
    DEMO_INTEGRATIONS,
    DEMO_LOGS,
    DEMO_RESPONSE_ACTIONS,
    DEMO_USERS,
    DEMO_VIRTUAL_MACHINES,
)


@pytest.fixture(autouse=True)
def restore_demo_state() -> None:
    alerts_snapshot = deepcopy(DEMO_ALERTS)
    blocked_ips_snapshot = deepcopy(DEMO_BLOCKED_IPS)
    incidents_snapshot = deepcopy(DEMO_INCIDENTS)
    integrations_snapshot = deepcopy(DEMO_INTEGRATIONS)
    logs_snapshot = deepcopy(DEMO_LOGS)
    response_actions_snapshot = deepcopy(DEMO_RESPONSE_ACTIONS)
    users_snapshot = deepcopy(DEMO_USERS)
    virtual_machines_snapshot = deepcopy(DEMO_VIRTUAL_MACHINES)

    yield

    DEMO_ALERTS[:] = alerts_snapshot
    DEMO_BLOCKED_IPS[:] = blocked_ips_snapshot
    DEMO_INCIDENTS[:] = incidents_snapshot
    DEMO_INTEGRATIONS[:] = integrations_snapshot
    DEMO_LOGS[:] = logs_snapshot
    DEMO_RESPONSE_ACTIONS[:] = response_actions_snapshot
    DEMO_USERS[:] = users_snapshot
    DEMO_VIRTUAL_MACHINES[:] = virtual_machines_snapshot


@pytest.fixture
def sqlite_storage(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'aegiscore-persistence.db'}", future=True)
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def run_with_sqlite(operation, fallback):
        db = testing_session_local()
        try:
            return operation(db)
        except SQLAlchemyError:
            db.rollback()
            return fallback()
        finally:
            db.close()

    monkeypatch.setattr(alerts_service, "run_with_optional_db", run_with_sqlite)
    monkeypatch.setattr(integrations_service, "run_with_optional_db", run_with_sqlite)
    monkeypatch.setattr(logs_service, "run_with_optional_db", run_with_sqlite)
    monkeypatch.setattr(incidents_service, "run_with_optional_db", run_with_sqlite)
    monkeypatch.setattr(response_actions_service, "run_with_optional_db", run_with_sqlite)
    monkeypatch.setattr(users_service, "run_with_optional_db", run_with_sqlite)
    monkeypatch.setattr(virtualbox_lab_service, "run_with_optional_db", run_with_sqlite)


def test_alert_log_and_incident_survive_memory_reset_via_database(sqlite_storage) -> None:
    created_log = logs_service.create_log_record(
        {
            "source": "lab-db-01",
            "source_tool": IntegrationTool.WAZUH,
            "severity": "medium",
            "event_type": "authentication",
            "raw_log": {
                "timestamp": "2026-03-22T11:05:00Z",
                "host": "lab-db-01",
                "message": "Failed password for invalid user dbuser from 10.0.0.50",
                "user": "dbuser",
                "source_ip": "10.0.0.50",
            },
        }
    )

    created_alert = alerts_service.create_alert(
        title="Database-backed suspicious login burst",
        description="Alert persisted through the database-backed alert service path.",
        source="lab-db-01",
        source_tool=IntegrationTool.WAZUH,
        severity=AlertSeverity.MEDIUM,
        confidence_score=0.77,
    )

    created_incident = incidents_service.create_incident(
        alert_id=created_alert["id"],
        notes="Incident persisted through the database-backed incident workflow.",
    )

    DEMO_LOGS[:] = [log for log in DEMO_LOGS if log["id"] != created_log["id"]]
    DEMO_ALERTS[:] = [alert for alert in DEMO_ALERTS if alert["id"] != created_alert["id"]]
    DEMO_INCIDENTS[:] = [incident for incident in DEMO_INCIDENTS if incident["id"] != created_incident["id"]]

    reloaded_log = logs_service.get_log_by_id(created_log["id"])
    reloaded_alert = alerts_service.get_alert_by_id(created_alert["id"])
    reloaded_incident = incidents_service.get_incident_by_id(created_incident["id"])

    assert reloaded_log["source"] == "lab-db-01"
    assert reloaded_alert["title"] == "Database-backed suspicious login burst"
    assert reloaded_incident["alert_id"] == created_alert["id"]

    dashboard_summary = get_dashboard_summary()
    assert dashboard_summary["total_alerts"] == len(DEMO_ALERTS) + 1
    assert dashboard_summary["open_incidents"] >= 1

    next_alert = alerts_service.create_alert(
        title="Second persisted alert after reload",
        description="This verifies ID generation continues from persisted records.",
        source="lab-db-02",
        source_tool=IntegrationTool.SURICATA,
        severity=AlertSeverity.LOW,
        confidence_score=0.61,
    )

    assert next_alert["id"] != created_alert["id"]
    assert next_alert["id"] > created_alert["id"]


def test_response_actions_and_integration_runtime_survive_memory_reset(sqlite_storage) -> None:
    action = response_actions_service.execute_response_action(
        alert_id="alert-001",
        action_type=ResponseActionType.BLOCK_SOURCE_IP,
        actor={"id": "user-admin", "full_name": "AegisCore Admin"},
    )
    assert action["status"] == "completed"

    import_result = import_hydra_results(
        [
            {
                "target_system": "lab-hydra-01",
                "protocol": "ssh",
                "result_summary": "Repeated match threshold crossed during authorized lab assessment",
                "timestamp": "2026-03-22T12:05:00Z",
                "notes": "Persistence verification import",
            }
        ]
    )
    assert import_result["imported_alert_count"] == 1

    original_hydra_integration = deepcopy(
        next(
            integration
            for integration in DEMO_INTEGRATIONS
            if integration["tool_name"] == IntegrationTool.HYDRA
        )
    )

    DEMO_RESPONSE_ACTIONS.clear()
    DEMO_BLOCKED_IPS.clear()
    for integration in DEMO_INTEGRATIONS:
        if integration["tool_name"] == IntegrationTool.HYDRA:
            integration.update(
                {
                    "last_import_at": original_hydra_integration.get("last_import_at"),
                    "last_import_message": original_hydra_integration.get("last_import_message"),
                }
            )

    response_history = response_actions_service.list_response_actions("alert-001")
    history_types = [item["action_type"] for item in response_history["items"]]
    assert ResponseActionType.BLOCK_SOURCE_IP in history_types

    suggestions = {
        item["action_type"]: item for item in response_history["recommended_actions"]
    }
    assert suggestions[ResponseActionType.BLOCK_SOURCE_IP]["available"] is False

    hydra_status = integrations_service.get_augmented_integration_by_tool(IntegrationTool.HYDRA)
    assert hydra_status["last_import_message"] == import_result["message"]
    assert hydra_status["last_import_at"] is not None


def test_user_auth_and_virtualbox_inventory_survive_memory_reset(sqlite_storage) -> None:
    admin_user = deepcopy(next(user for user in DEMO_USERS if user["id"] == "user-admin"))
    users_service.persist_user_record(admin_user)

    login_result = auth_service.login_user(admin_user["email"], "password")
    assert login_result["id"] == admin_user["id"]

    created_vm = virtualbox_lab_service.create_virtual_machine(
        {
            "vm_name": "lab-monitor-05",
            "role": "Monitoring Relay VM",
            "os_type": "Ubuntu 24.04",
            "ip_address": "10.10.0.45",
            "status": VirtualMachineStatus.PROVISIONING,
            "notes": "Temporary runtime persistence verification VM.",
        }
    )

    updated_vm = virtualbox_lab_service.update_virtual_machine(
        created_vm["id"],
        {
            "status": VirtualMachineStatus.RUNNING,
            "notes": "Provisioning completed and ready for lab monitoring.",
        },
    )
    assert updated_vm["status"] == VirtualMachineStatus.RUNNING

    DEMO_USERS.clear()
    DEMO_VIRTUAL_MACHINES.clear()

    persisted_user = auth_service.get_current_user_from_payload({"sub": admin_user["email"]})
    assert persisted_user["full_name"] == "AegisCore Admin"

    listed_users = auth_service.list_demo_users()
    assert any(user["id"] == admin_user["id"] for user in listed_users)

    reloaded_vm = virtualbox_lab_service.get_virtual_machine_by_id(created_vm["id"])
    assert reloaded_vm["notes"] == "Provisioning completed and ready for lab monitoring."

    listed_vms = virtualbox_lab_service.list_virtual_machines()
    assert any(vm["id"] == created_vm["id"] for vm in listed_vms)

    next_vm = virtualbox_lab_service.create_virtual_machine(
        {
            "vm_name": "lab-monitor-06",
            "role": "Spare Collector VM",
            "os_type": "Debian 12",
            "ip_address": "10.10.0.46",
            "status": VirtualMachineStatus.STOPPED,
            "notes": "Used to verify VM IDs continue from persisted runtime records.",
        }
    )
    assert next_vm["id"] != created_vm["id"]
    assert next_vm["id"] > created_vm["id"]

    virtualbox_status = integrations_service.get_augmented_integration_by_tool(
        IntegrationTool.VIRTUALBOX
    )
    assert virtualbox_status["status"] == IntegrationHealth.DEGRADED
    assert virtualbox_status["last_import_message"] == (
        "Inventory updated. 2 VirtualBox VMs are now tracked."
    )


def test_persisted_alerts_drive_anomaly_summary_and_live_ready_payload(sqlite_storage) -> None:
    created_alert = alerts_service.create_alert(
        title="Persisted websocket readiness verification",
        description="Ensures persisted alerts remain visible to live-ready and anomaly summary flows.",
        source="lab-live-01",
        source_tool=IntegrationTool.WAZUH,
        severity=AlertSeverity.CRITICAL,
        confidence_score=0.97,
    )

    DEMO_ALERTS[:] = [alert for alert in DEMO_ALERTS if alert["id"] != created_alert["id"]]

    anomaly_summary = get_anomaly_summary(limit=100)
    assert any(
        alert["id"] == created_alert["id"]
        for alert in anomaly_summary["top_anomalous_alerts"]
    )

    ready_payload = build_alert_stream_ready_payload()
    assert ready_payload["latest_alert"] is not None
    assert ready_payload["latest_alert"]["id"] == created_alert["id"]
