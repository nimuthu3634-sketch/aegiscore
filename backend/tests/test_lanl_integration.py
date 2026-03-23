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


def test_lanl_auth_upload_generates_logs_and_redteam_alerts() -> None:
    headers = _admin_headers()

    response = client.post(
        "/integrations/lanl/import",
        headers=headers,
        files={
            "dataset_file": (
                "auth.txt",
                "\n".join(
                    [
                        "930,U24@DOM1,U24@DOM1,C17693,C612,Kerberos,Network,LogOn,Success",
                        "931,U24@DOM1,U24@DOM1,C17693,C612,Kerberos,Network,LogOn,Failure",
                        "932,U24@DOM1,U24@DOM1,C17693,C612,Kerberos,Network,LogOn,Failure",
                        "933,U24@DOM1,U24@DOM1,C17693,C612,Kerberos,Network,LogOn,Failure",
                    ]
                ),
                "text/plain",
            ),
            "redteam_file": ("redteam.txt", "930,U24,C17693,C612", "text/plain"),
        },
        data={"dataset_type": "auth", "max_records": "50"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["dataset_type"] == "auth"
    assert payload["processed_record_count"] == 4
    assert payload["imported_log_count"] == 4
    assert payload["imported_alert_count"] == 2
    assert payload["redteam_match_count"] == 1

    lanl_alerts = [alert for alert in DEMO_ALERTS if alert["source_tool"] == "lanl"]
    assert any(alert["event_type"] == "compromise" for alert in lanl_alerts)
    assert any(alert["event_type"] == "authentication" for alert in lanl_alerts)

    lanl_logs = [log_entry for log_entry in DEMO_LOGS if log_entry["source_tool"] == "lanl"]
    assert len(lanl_logs) == 4
    assert all(log_entry["lab_only"] is False for log_entry in lanl_logs)


def test_lanl_status_reflects_uploaded_records() -> None:
    headers = _admin_headers()

    upload_response = client.post(
        "/integrations/lanl/import",
        headers=headers,
        files={
            "dataset_file": (
                "dns.txt",
                "\n".join([f"{600 + index},C101,asset-{index}" for index in range(30)]),
                "text/plain",
            ),
        },
        data={"dataset_type": "dns", "max_records": "100"},
    )
    assert upload_response.status_code == 201

    status_response = client.get("/integrations/lanl/status", headers=headers)
    assert status_response.status_code == 200
    payload = status_response.json()

    assert payload["tool_name"] == "lanl"
    assert payload["status"] == "connected"
    assert payload["imported_log_count"] == 30
    assert payload["imported_alert_count"] >= 1
    assert "auth" in payload["supported_dataset_types"]
    assert payload["redteam_supported"] is True
