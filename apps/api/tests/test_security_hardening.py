from __future__ import annotations

from starlette.websockets import WebSocketDisconnect


def test_import_rejects_unsupported_extension_with_request_id(client, admin_token):
    response = client.post(
        "/api/v1/integrations/wazuh/import",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={"file": ("telemetry.exe", b"{}", "application/octet-stream")},
    )

    assert response.status_code == 400
    payload = response.json()
    assert "Unsupported file type" in payload["detail"]
    assert payload["request_id"]


def test_websocket_accepts_cookie_authenticated_sessions(client, login_as):
    response = login_as("admin@example.com", "Admin123!")

    assert response.status_code == 200

    with client.websocket_connect("/api/v1/ws/alerts") as websocket:
        payload = websocket.receive_json()
        assert payload["event"] == "connected"
        assert payload["user"] == "admin@example.com"


def test_websocket_rejects_anonymous_connections(client):
    try:
        with client.websocket_connect("/api/v1/ws/alerts"):
            raise AssertionError("Anonymous websocket connection should not succeed")
    except WebSocketDisconnect as error:
        assert error.code == 4401
