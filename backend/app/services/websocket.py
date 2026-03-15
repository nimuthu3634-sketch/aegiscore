from app.services.mock_store import DEMO_ALERTS


def build_alert_stream_payload() -> dict:
    latest_alert = DEMO_ALERTS[0] if DEMO_ALERTS else None
    return {
        "event": "alerts_stream_ready",
        "message": "WebSocket scaffold connected.",
        "latest_alert_id": latest_alert["id"] if latest_alert else None,
    }
