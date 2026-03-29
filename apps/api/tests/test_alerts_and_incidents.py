from __future__ import annotations


def test_alert_to_incident_flow(client, analyst_token):
    create_alert = client.post(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={
            "title": "Suspicious RDP exposure",
            "description": "Unexpected RDP port opened on a finance workstation",
            "source": "nmap",
            "severity": "high",
            "asset_hostname": "finance-ws-01",
            "asset_ip": "10.20.10.15",
            "tags": ["rdp", "exposure"],
            "raw_payload": {"port": 3389},
            "parsed_payload": {"port": 3389},
        },
    )

    assert create_alert.status_code == 201
    alert_id = create_alert.json()["id"]

    comment = client.post(
        f"/api/v1/alerts/{alert_id}/comments",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"body": "Validating whether this is an approved remote support exception."},
    )
    assert comment.status_code == 201

    create_incident = client.post(
        f"/api/v1/alerts/{alert_id}/incident",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={
            "title": "Investigate suspicious RDP exposure",
            "summary": "Need to confirm whether the open port is authorized.",
            "priority": "P2",
            "linked_alert_ids": [],
            "evidence": [],
        },
    )

    assert create_incident.status_code == 201
    assert create_incident.json()["linked_alerts"][0]["id"] == alert_id
