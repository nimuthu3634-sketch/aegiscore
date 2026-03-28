from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.mock_store import DEMO_ALERTS, DEMO_INTEGRATIONS, DEMO_LOGS

client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_demo_state() -> None:
    alerts_snapshot = deepcopy(DEMO_ALERTS)
    integrations_snapshot = deepcopy(DEMO_INTEGRATIONS)
    logs_snapshot = deepcopy(DEMO_LOGS)

    yield

    DEMO_ALERTS[:] = alerts_snapshot
    DEMO_INTEGRATIONS[:] = integrations_snapshot
    DEMO_LOGS[:] = logs_snapshot


def _admin_headers() -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"email": "admin@aegiscore.local", "password": "password"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_integrations_status_only_exposes_proposal_supported_tools() -> None:
    response = client.get("/integrations/status", headers=_admin_headers())

    assert response.status_code == 200
    tool_names = {item["tool_name"] for item in response.json()}
    assert tool_names == {"wazuh", "suricata", "nmap", "hydra"}


def test_wazuh_and_suricata_imports_create_alerts_logs_and_status_updates() -> None:
    headers = _admin_headers()

    wazuh_response = client.post(
        "/integrations/wazuh/import",
        json={
            "alerts": [
                {
                    "id": "wazuh-proposal-001",
                    "timestamp": "2026-03-24T08:10:00Z",
                    "agent": {"name": "lab-endpoint-11"},
                    "rule": {
                        "level": 9,
                        "description": "Repeated failed SSH logins detected",
                        "groups": ["authentication_failed", "sshd"],
                    },
                    "full_log": "Failed password for invalid user trainee from 10.0.0.55",
                    "data": {"srcip": "10.0.0.55", "user": "trainee"},
                }
            ]
        },
        headers=headers,
    )
    assert wazuh_response.status_code == 201
    assert wazuh_response.json()["imported_alert_count"] == 1
    assert any(alert["source_tool"] == "wazuh" and alert["source"] == "lab-endpoint-11" for alert in DEMO_ALERTS)
    assert any(log_entry["source_tool"] == "wazuh" and log_entry["source"] == "lab-endpoint-11" for log_entry in DEMO_LOGS)

    suricata_response = client.post(
        "/integrations/suricata/import",
        json={
            "events": [
                {
                    "timestamp": "2026-03-24T08:15:00Z",
                    "event_type": "alert",
                    "src_ip": "10.10.30.44",
                    "dest_ip": "172.16.11.20",
                    "dest_port": 3389,
                    "proto": "TCP",
                    "sensor_name": "sensor-west-01",
                    "alert": {
                        "signature": "ET SCAN Potential internal RDP reconnaissance activity",
                        "category": "Attempted Information Leak",
                        "severity": 3,
                    },
                }
            ]
        },
        headers=headers,
    )
    assert suricata_response.status_code == 201
    assert suricata_response.json()["imported_alert_count"] == 1
    assert any(
        alert["source_tool"] == "suricata" and alert["source"] == "sensor-west-01"
        for alert in DEMO_ALERTS
    )
    assert any(
        log_entry["source_tool"] == "suricata" and log_entry["source"] == "sensor-west-01"
        for log_entry in DEMO_LOGS
    )

    wazuh_status = client.get("/integrations/wazuh/status", headers=headers)
    suricata_status = client.get("/integrations/suricata/status", headers=headers)

    assert wazuh_status.status_code == 200
    assert suricata_status.status_code == 200
    assert wazuh_status.json()["imported_alert_count"] >= 1
    assert suricata_status.json()["imported_alert_count"] >= 1
