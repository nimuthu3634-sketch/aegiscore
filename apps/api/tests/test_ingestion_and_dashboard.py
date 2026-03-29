from __future__ import annotations

from pathlib import Path


def test_wazuh_import_updates_dashboard(client, admin_token):
    sample = Path(__file__).resolve().parents[2] / "docs" / "sample-wazuh-alerts.json"
    with sample.open("rb") as handle:
        response = client.post(
            "/api/v1/integrations/wazuh/import",
            headers={"Authorization": f"Bearer {admin_token}"},
            files={"file": ("sample-wazuh-alerts.json", handle, "application/json")},
        )

    assert response.status_code == 202
    assert response.json()["alerts_created"] >= 1

    dashboard = client.get("/api/v1/dashboard/summary", headers={"Authorization": f"Bearer {admin_token}"})
    assert dashboard.status_code == 200
    assert dashboard.json()["kpis"]["open_alerts"] >= 1
