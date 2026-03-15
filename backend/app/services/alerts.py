from math import ceil

from fastapi import HTTPException, status

from app.services.anomaly import apply_anomaly_scoring, ensure_demo_alerts_scored
from app.core.enums import AlertSeverity, AlertStatus, IntegrationTool
from app.services.mock_store import DEMO_ALERTS
from app.services.websocket import broadcast_alert_created
from app.utils.time import utc_now


def _sorted_alerts() -> list[dict]:
    ensure_demo_alerts_scored()
    return sorted(DEMO_ALERTS, key=lambda alert: alert["created_at"], reverse=True)


def _matches_filters(
    alert: dict,
    severity: AlertSeverity | None,
    status_filter: AlertStatus | None,
    source_tool: IntegrationTool | None,
    search: str | None,
) -> bool:
    if severity and alert["severity"] != severity:
        return False

    if status_filter and alert["status"] != status_filter:
        return False

    if source_tool and alert["source_tool"] != source_tool:
        return False

    if not search:
        return True

    search_value = search.strip().lower()
    if not search_value:
        return True

    searchable_fields = [
        alert["title"],
        alert["description"],
        alert["source"],
        alert["source_tool"],
    ]
    return any(search_value in field.lower() for field in searchable_fields)


def list_alerts(
    *,
    severity: AlertSeverity | None = None,
    status_filter: AlertStatus | None = None,
    source_tool: IntegrationTool | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    filtered_alerts = [
        alert
        for alert in _sorted_alerts()
        if _matches_filters(alert, severity, status_filter, source_tool, search)
    ]

    total_items = len(filtered_alerts)
    total_pages = max(1, ceil(total_items / page_size)) if total_items else 1
    start_index = (page - 1) * page_size
    end_index = start_index + page_size

    return {
        "items": filtered_alerts[start_index:end_index],
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
    }


def get_alert_by_id(alert_id: str) -> dict:
    ensure_demo_alerts_scored()
    alert = next((item for item in DEMO_ALERTS if item["id"] == alert_id), None)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")

    return alert


def create_alert(
    *,
    title: str,
    description: str,
    source: str,
    source_tool: IntegrationTool | str,
    severity: AlertSeverity,
    status_value: AlertStatus = AlertStatus.NEW,
    confidence_score: float = 0.75,
    created_at=None,
    extra_fields: dict | None = None,
) -> dict:
    alert_record = {
        "id": f"alert-{len(DEMO_ALERTS) + 1:03d}",
        "title": title,
        "description": description,
        "source": source,
        "source_tool": source_tool,
        "severity": severity,
        "status": status_value,
        "confidence_score": confidence_score,
        "created_at": created_at or utc_now(),
    }

    if extra_fields:
        alert_record.update(extra_fields)

    apply_anomaly_scoring(alert_record, reference_alerts=DEMO_ALERTS)
    DEMO_ALERTS.append(alert_record)
    broadcast_alert_created(alert_record)
    return alert_record


def update_alert_status(alert_id: str, alert_status: AlertStatus) -> dict:
    alert = get_alert_by_id(alert_id)
    alert["status"] = alert_status
    return alert
