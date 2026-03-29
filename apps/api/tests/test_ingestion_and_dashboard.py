from __future__ import annotations

from pathlib import Path

from app.services import integrations as integration_service


def test_wazuh_import_updates_dashboard(client, admin_token):
    sample = Path(__file__).resolve().parents[3] / "docs" / "sample-wazuh-alerts.json"
    with sample.open("rb") as handle:
        response = client.post(
            "/api/v1/integrations/wazuh/import",
            headers={"Authorization": f"Bearer {admin_token}"},
            files={"file": ("sample-wazuh-alerts.json", handle, "application/json")},
        )

    assert response.status_code == 202
    payload = response.json()
    assert payload["mode"] == "import"
    assert payload["input_format"] == "json"
    assert payload["alerts_created"] >= 1

    dashboard = client.get("/api/v1/dashboard/summary", headers={"Authorization": f"Bearer {admin_token}"})
    assert dashboard.status_code == 200
    assert dashboard.json()["kpis"]["open_alerts"] >= 1


def test_suricata_sync_uses_config_and_records_run(client, admin_token, monkeypatch):
    sample = Path(__file__).resolve().parents[3] / "docs" / "sample-suricata-events.json"

    def fake_fetch_remote_payload(_integration):
        return sample.read_bytes(), "application/json"

    monkeypatch.setattr(integration_service, "fetch_remote_payload", fake_fetch_remote_payload)

    update = client.patch(
        "/api/v1/integrations/suricata",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "endpoint_url": "https://suricata.lab.local/eve/export",
            "auth_type": "bearer",
            "api_token": "super-secret-token",
            "verify_tls": False,
            "lookback_minutes": 90,
        },
    )
    assert update.status_code == 200
    assert update.json()["configuration"]["has_api_token"] is True
    assert update.json()["configuration"]["endpoint_url"] == "https://suricata.lab.local/eve/export"

    response = client.post(
        "/api/v1/integrations/suricata/sync",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["mode"] == "sync"
    assert payload["alerts_created"] >= 1

    integration = client.get("/api/v1/integrations/suricata", headers={"Authorization": f"Bearer {admin_token}"})
    assert integration.status_code == 200
    assert integration.json()["connection_status"] == "connected"
    assert integration.json()["runs"][0]["mode"] == "sync"


def test_nmap_xml_import_marks_lab_data(client, admin_token):
    xml_payload = """
    <nmaprun startstr="2026-03-29T10:00:00Z">
      <host>
        <status state="up" />
        <address addr="10.10.10.5" addrtype="ipv4" />
        <hostnames><hostname name="lab-gateway-01" /></hostnames>
        <ports>
          <port protocol="tcp" portid="22">
            <state state="open" />
            <service name="ssh" />
          </port>
          <port protocol="tcp" portid="3389">
            <state state="open" />
            <service name="ms-wbt-server" />
          </port>
        </ports>
      </host>
    </nmaprun>
    """.strip()

    response = client.post(
        "/api/v1/integrations/nmap/import",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={"file": ("lab-nmap.xml", xml_payload, "application/xml")},
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["mode"] == "import"
    assert payload["imported_lab_data"] is True
    assert payload["input_format"] == "xml"

    logs = client.get("/api/v1/logs?source=nmap", headers={"Authorization": f"Bearer {admin_token}"})
    assert logs.status_code == 200
    assert logs.json()["items"][0]["parsed_payload"]["lab_imported"] is True


def test_hydra_text_import_parses_valid_credentials(client, admin_token):
    hydra_text = "[22][ssh] host: lab-ssh-01 login: analyst_demo password: Welcome123!"

    response = client.post(
        "/api/v1/integrations/hydra/import",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={"file": ("hydra-output.txt", hydra_text, "text/plain")},
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["imported_lab_data"] is True
    assert payload["input_format"] == "txt"
    assert payload["alerts_created"] >= 1

    logs = client.get("/api/v1/logs?source=hydra", headers={"Authorization": f"Bearer {admin_token}"})
    assert logs.status_code == 200
    assert logs.json()["items"][0]["parsed_payload"]["has_password_match"] is True


def test_nmap_sync_is_rejected(client, admin_token):
    response = client.post(
        "/api/v1/integrations/nmap/sync",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 400
    assert "import-only" in response.json()["detail"]
