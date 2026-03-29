from __future__ import annotations


def test_viewer_cannot_create_alert(client):
    login = client.post("/api/v1/auth/login", json={"email": "viewer@example.com", "password": "Viewer123!"})
    token = login.json()["access_token"]

    response = client.post(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Viewer attempted change",
            "description": "Should be blocked",
            "source": "wazuh",
            "severity": "low",
        },
    )

    assert response.status_code == 403


def test_health_reports_database_and_redis_status(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["app"]["status"] == "ok"
    assert payload["database"]["status"] == "ok"
    assert payload["redis"]["status"] in {"ok", "error"}
