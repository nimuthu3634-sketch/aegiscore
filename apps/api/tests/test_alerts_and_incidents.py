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
            "description": "Need to confirm whether the open port is authorized.",
            "priority": "P2",
            "linked_alert_ids": [],
            "evidence": [],
        },
    )

    assert create_incident.status_code == 201
    assert create_incident.json()["linked_alerts"][0]["id"] == alert_id
    assert create_incident.json()["timeline_events"][0]["event_type"] == "status-change"


def test_alert_response_action_flow(client, analyst_token):
    create_alert = client.post(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={
            "title": "Malicious callback detected",
            "description": "Outbound connection to a known bad IP",
            "source": "suricata",
            "severity": "critical",
            "asset_hostname": "lab-host-01",
            "asset_ip": "10.20.10.25",
            "tags": ["network", "containment"],
            "raw_payload": {"src_ip": "198.51.100.7"},
            "parsed_payload": {"src_ip": "198.51.100.7", "username": "analyst_demo"},
        },
    )

    assert create_alert.status_code == 201
    alert_id = create_alert.json()["id"]

    response = client.post(
        f"/api/v1/alerts/{alert_id}/respond",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"action": "block_ip", "reason": "Observed repeated callbacks from the same indicator."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["action"] == "block_ip"
    assert payload["status"] == "simulated"
    assert payload["target"]["ip_address"] == "198.51.100.7"
    assert payload["follow_up"]

    alert = client.get(f"/api/v1/alerts/{alert_id}", headers={"Authorization": f"Bearer {analyst_token}"})
    assert alert.status_code == 200
    alert_payload = alert.json()
    assert alert_payload["status"] == "investigating"
    assert any("Block source IP recorded." in entry["body"] for entry in alert_payload["comments"])
