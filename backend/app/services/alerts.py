from fastapi import HTTPException, status

from app.services.mock_store import DEMO_ALERTS


def list_alerts() -> list[dict]:
    return DEMO_ALERTS


def get_alert_by_id(alert_id: str) -> dict:
    alert = next((item for item in DEMO_ALERTS if item["id"] == alert_id), None)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")

    return alert
