from fastapi import HTTPException, status

from app.core.enums import AlertSeverity, IncidentStatus, UserRole
from app.services.alerts import get_alert_by_id
from app.services.mock_store import DEMO_INCIDENTS, DEMO_USERS
from app.utils.time import utc_now


def _sorted_incidents() -> list[dict]:
    return sorted(
        DEMO_INCIDENTS,
        key=lambda incident: incident.get("updated_at") or incident["opened_at"],
        reverse=True,
    )


def _get_available_assignees() -> list[dict]:
    return [
        {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user["role"],
        }
        for user in DEMO_USERS
        if user["role"] == UserRole.ANALYST and user.get("is_active", False)
    ]


def _validate_assignee(assigned_to_user_id: str | None) -> str | None:
    if assigned_to_user_id is None:
        return None

    assignee = next((user for user in DEMO_USERS if user["id"] == assigned_to_user_id), None)
    if (
        not assignee
        or assignee["role"] != UserRole.ANALYST
        or not assignee.get("is_active", False)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assigned user must be an active analyst.",
        )

    return assigned_to_user_id


def _serialize_incident(incident: dict) -> dict:
    user_lookup = {user["id"]: user["full_name"] for user in DEMO_USERS}
    alert = get_alert_by_id(incident["alert_id"]) if incident.get("alert_id") else None

    return {
        "id": incident["id"],
        "alert_id": incident.get("alert_id"),
        "alert_title": alert["title"] if alert else None,
        "title": incident["title"],
        "priority": incident["priority"],
        "status": incident["status"],
        "notes": incident["notes"],
        "opened_at": incident["opened_at"],
        "updated_at": incident.get("updated_at") or incident["opened_at"],
        "closed_at": incident.get("closed_at"),
        "assigned_to_user_id": incident.get("assigned_to_user_id"),
        "assigned_to_name": user_lookup.get(incident.get("assigned_to_user_id")),
        "affected_asset": incident["affected_asset"],
        "source_tool": alert["source_tool"] if alert else None,
        "summary": incident.get("summary") or incident["notes"],
    }


def list_incidents(
    *,
    priority: AlertSeverity | None = None,
    status_filter: IncidentStatus | None = None,
    assignee_id: str | None = None,
) -> dict:
    incidents = []

    for incident in _sorted_incidents():
        if priority and incident["priority"] != priority:
            continue

        if status_filter and incident["status"] != status_filter:
            continue

        if assignee_id and incident.get("assigned_to_user_id") != assignee_id:
            continue

        incidents.append(_serialize_incident(incident))

    return {
        "items": incidents,
        "available_assignees": _get_available_assignees(),
        "total_items": len(incidents),
    }


def get_incident_by_id(incident_id: str) -> dict:
    incident = next((item for item in DEMO_INCIDENTS if item["id"] == incident_id), None)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")

    return _serialize_incident(incident)


def create_incident(
    *,
    alert_id: str,
    assigned_to_user_id: str | None = None,
    priority: AlertSeverity | None = None,
    notes: str = "",
) -> dict:
    if any(incident.get("alert_id") == alert_id for incident in DEMO_INCIDENTS):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An incident already exists for this alert.",
        )

    alert = get_alert_by_id(alert_id)
    assignee_id = _validate_assignee(assigned_to_user_id)
    timestamp = utc_now()
    incident_number = len(DEMO_INCIDENTS) + 1

    incident = {
        "id": f"incident-{incident_number:03d}",
        "alert_id": alert_id,
        "assigned_to_user_id": assignee_id,
        "priority": priority or alert["severity"],
        "status": IncidentStatus.OPEN,
        "notes": notes.strip() or f"Incident created from alert {alert_id} for analyst review.",
        "title": alert["title"],
        "summary": alert["description"],
        "affected_asset": alert["source"],
        "updated_at": timestamp,
        "opened_at": timestamp,
        "closed_at": None,
    }
    DEMO_INCIDENTS.insert(0, incident)
    return _serialize_incident(incident)


def update_incident(incident_id: str, updates: dict) -> dict:
    incident = next((item for item in DEMO_INCIDENTS if item["id"] == incident_id), None)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")

    if "assigned_to_user_id" in updates:
        incident["assigned_to_user_id"] = _validate_assignee(updates["assigned_to_user_id"])

    if "priority" in updates and updates["priority"] is not None:
        incident["priority"] = updates["priority"]

    if "notes" in updates and updates["notes"] is not None:
        incident["notes"] = updates["notes"]

    if "status" in updates and updates["status"] is not None:
        incident["status"] = updates["status"]
        if updates["status"] == IncidentStatus.RESOLVED:
            incident["closed_at"] = utc_now()
        else:
            incident["closed_at"] = None

    incident["updated_at"] = utc_now()
    return _serialize_incident(incident)
