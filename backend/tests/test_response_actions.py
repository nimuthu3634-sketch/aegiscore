from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.mock_store import (
    DEMO_ALERTS,
    DEMO_BLOCKED_IPS,
    DEMO_DISABLED_ACCOUNTS,
    DEMO_INCIDENTS,
    DEMO_INTEGRATIONS,
    DEMO_ISOLATED_ASSETS,
    DEMO_LOGS,
    DEMO_RESPONSE_ACTIONS,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_demo_state() -> None:
    snapshots = {
        "alerts": deepcopy(DEMO_ALERTS),
        "blocked_ips": deepcopy(DEMO_BLOCKED_IPS),
        "disabled_accounts": deepcopy(DEMO_DISABLED_ACCOUNTS),
        "incidents": deepcopy(DEMO_INCIDENTS),
        "integrations": deepcopy(DEMO_INTEGRATIONS),
        "isolated_assets": deepcopy(DEMO_ISOLATED_ASSETS),
        "logs": deepcopy(DEMO_LOGS),
        "response_actions": deepcopy(DEMO_RESPONSE_ACTIONS),
    }

    yield

    DEMO_ALERTS[:] = snapshots["alerts"]
    DEMO_BLOCKED_IPS[:] = snapshots["blocked_ips"]
    DEMO_DISABLED_ACCOUNTS[:] = snapshots["disabled_accounts"]
    DEMO_INCIDENTS[:] = snapshots["incidents"]
    DEMO_INTEGRATIONS[:] = snapshots["integrations"]
    DEMO_ISOLATED_ASSETS[:] = snapshots["isolated_assets"]
    DEMO_LOGS[:] = snapshots["logs"]
    DEMO_RESPONSE_ACTIONS[:] = snapshots["response_actions"]


def _admin_headers() -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"email": "admin@aegiscore.local", "password": "password"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_response_actions_list_exposes_safe_suggestions_for_auth_alert() -> None:
    response = client.get("/alerts/alert-001/response-actions", headers=_admin_headers())

    assert response.status_code == 200
    payload = response.json()
    suggestions = {item["action_type"]: item for item in payload["recommended_actions"]}

    assert suggestions["create_incident"]["available"] is True
    assert suggestions["mark_investigating"]["available"] is True
    assert suggestions["block_source_ip"]["target_label"] == "10.0.0.22"
    assert suggestions["disable_account"]["target_label"] == "analyst"


def test_block_source_ip_action_updates_alert_and_records_audit_history() -> None:
    headers = _admin_headers()

    response = client.post(
        "/alerts/alert-001/response-actions",
        json={"action_type": "block_source_ip"},
        headers=headers,
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["execution_mode"] == "manual"
    assert payload["target_label"] == "10.0.0.22"

    alert_response = client.get("/alerts/alert-001", headers=headers)
    assert alert_response.status_code == 200
    assert alert_response.json()["status"] == "investigating"

    history_response = client.get("/alerts/alert-001/response-actions", headers=headers)
    assert history_response.status_code == 200
    history = history_response.json()["items"]
    assert history[0]["action_type"] == "block_source_ip"
    assert history[0]["result_summary"] == "Source IP 10.0.0.22 was added to the simulated lab blocklist."


def test_high_risk_import_automatically_escalates_into_incident_workflow() -> None:
    headers = _admin_headers()

    response = client.post(
        "/integrations/nmap/import",
        json={
            "results": [
                {
                    "host": "lab-auto-01",
                    "open_ports": [{"port": 3389, "service_name": "rdp", "protocol": "tcp"}],
                    "service_names": ["rdp"],
                    "scan_timestamp": "2026-03-22T10:15:00Z",
                    "scan_notes": "Critical port exposure used to validate auto response.",
                }
            ]
        },
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["imported_alert_count"] == 1

    created_alert = next(alert for alert in DEMO_ALERTS if alert["source"] == "lab-auto-01")
    assert created_alert["status"] == "investigating"

    response_actions = client.get(
        f"/alerts/{created_alert['id']}/response-actions",
        headers=headers,
    )
    assert response_actions.status_code == 200
    history = response_actions.json()["items"]

    action_modes = {(item["action_type"], item["execution_mode"]) for item in history}
    assert ("mark_investigating", "automated") in action_modes
    assert ("create_incident", "automated") in action_modes

    linked_incident = next(
        incident for incident in DEMO_INCIDENTS if incident.get("alert_id") == created_alert["id"]
    )
    assert linked_incident["title"] == created_alert["title"]


def test_alert_event_type_filter_and_import_context_are_exposed_via_api() -> None:
    headers = _admin_headers()

    filtered_response = client.get("/alerts?event_type=authentication", headers=headers)
    assert filtered_response.status_code == 200
    filtered_items = filtered_response.json()["items"]
    assert any(
        item["id"] == "alert-001" and item["event_type"] == "authentication"
        for item in filtered_items
    )

    import_response = client.post(
        "/integrations/nmap/import",
        json={
            "results": [
                {
                    "host": "lab-context-01",
                    "open_ports": [{"port": 3389, "service_name": "rdp", "protocol": "tcp"}],
                    "service_names": ["rdp"],
                    "scan_timestamp": "2026-03-23T09:45:00Z",
                    "scan_notes": "API context exposure verification import",
                }
            ]
        },
        headers=headers,
    )
    assert import_response.status_code == 201

    created_alert = next(alert for alert in DEMO_ALERTS if alert["source"] == "lab-context-01")
    created_log = next(log_entry for log_entry in DEMO_LOGS if log_entry["source"] == "lab-context-01")

    alert_detail = client.get(f"/alerts/{created_alert['id']}", headers=headers)
    assert alert_detail.status_code == 200
    alert_payload = alert_detail.json()
    assert alert_payload["event_type"] == "scan_result"
    assert alert_payload["lab_only"] is True
    assert alert_payload["parser_status"] == "normalized"
    assert alert_payload["integration_ref"] == created_alert["integration_ref"]

    log_detail = client.get(f"/logs/{created_log['id']}", headers=headers)
    assert log_detail.status_code == 200
    log_payload = log_detail.json()
    assert log_payload["event_type"] == "scan_result"
    assert log_payload["lab_only"] is True
    assert log_payload["parser_status"] == "normalized"
    assert log_payload["integration_ref"] == created_log["integration_ref"]
