from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.enums import UserRole
from app.core.security import create_access_token
from app.main import app

client = TestClient(app)


def test_alert_stream_rejects_unauthenticated_connections() -> None:
    try:
        with client.websocket_connect("/ws/alerts") as websocket:
            websocket.receive_json()
    except WebSocketDisconnect as error:
        assert error.code == 1008
    else:  # pragma: no cover - defensive guard
        raise AssertionError("Unauthenticated websocket connection should be rejected.")


def test_alert_stream_accepts_authenticated_connections() -> None:
    token = create_access_token(
        subject="admin@aegiscore.local",
        role=UserRole.ADMIN,
    )

    with client.websocket_connect(f"/ws/alerts?token={token}") as websocket:
        payload = websocket.receive_json()

    assert payload["event"] == "alerts_stream_ready"
    assert "message" in payload
