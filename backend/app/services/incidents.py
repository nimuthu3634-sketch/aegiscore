from fastapi import HTTPException, status
from sqlalchemy import select

from app.core.enums import AlertSeverity, IncidentStatus, UserRole
from app.models.incident import Incident
from app.services.alerts import get_alert_by_id
from app.services.mock_store import DEMO_INCIDENTS
from app.services.persistence import run_with_optional_db
from app.services.record_ids import next_prefixed_id
from app.services.users import get_user_by_id, get_user_name_lookup, list_active_analysts
from app.utils.time import ensure_utc, utc_now


def _incident_from_model(incident: Incident) -> dict:
    return {
        "id": incident.id,
        "alert_id": incident.alert_id,
        "assigned_to_user_id": incident.assigned_to_user_id,
        "priority": incident.priority,
        "status": incident.status,
        "notes": incident.notes,
        "opened_at": ensure_utc(incident.opened_at),
        "updated_at": ensure_utc(incident.closed_at or incident.opened_at),
        "closed_at": ensure_utc(incident.closed_at),
    }


def _load_persisted_incidents() -> list[dict]:
    def operation(db) -> list[dict]:
        incidents = db.scalars(select(Incident).order_by(Incident.opened_at.desc())).all()
        return [_incident_from_model(incident) for incident in incidents]

    return run_with_optional_db(operation, lambda: [])


def load_incident_records() -> list[dict]:
    merged_incidents = {incident["id"]: dict(incident) for incident in DEMO_INCIDENTS}

    for persisted_incident in _load_persisted_incidents():
        if persisted_incident["id"] in merged_incidents:
            merged_incidents[persisted_incident["id"]] = {
                **merged_incidents[persisted_incident["id"]],
                **persisted_incident,
            }
        else:
            merged_incidents[persisted_incident["id"]] = persisted_incident

    filtered_incidents: list[dict] = []
    for incident in merged_incidents.values():
        alert_id = incident.get("alert_id")
        if not alert_id:
            filtered_incidents.append(incident)
            continue

        try:
            get_alert_by_id(alert_id)
        except HTTPException:
            continue

        filtered_incidents.append(incident)

    return filtered_incidents


def _persist_incident_record(incident_record: dict) -> None:
    def operation(db) -> None:
        db.merge(
            Incident(
                id=incident_record["id"],
                alert_id=incident_record.get("alert_id"),
                assigned_to_user_id=incident_record.get("assigned_to_user_id"),
                priority=incident_record["priority"],
                status=incident_record["status"],
                notes=incident_record.get("notes", ""),
                opened_at=incident_record["opened_at"],
                closed_at=incident_record.get("closed_at"),
            )
        )
        db.commit()

    run_with_optional_db(operation, lambda: None)


def _sorted_incidents() -> list[dict]:
    return sorted(
        load_incident_records(),
        key=lambda incident: incident.get("updated_at") or incident["opened_at"],
        reverse=True,
    )


def _get_available_assignees() -> list[dict]:
    return list_active_analysts()


def _validate_assignee(assigned_to_user_id: str | None) -> str | None:
    if assigned_to_user_id is None:
        return None

    assignee = get_user_by_id(assigned_to_user_id)
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
    user_lookup = get_user_name_lookup()
    alert = get_alert_by_id(incident["alert_id"]) if incident.get("alert_id") else None
    title = incident.get("title") or (alert["title"] if alert else "Incident review")
    affected_asset = incident.get("affected_asset") or (alert["source"] if alert else "Unknown asset")
    summary = incident.get("summary") or (alert["description"] if alert else incident["notes"])
    alert_finding_metadata = (
        alert.get("finding_metadata", {})
        if alert and isinstance(alert.get("finding_metadata"), dict)
        else {}
    )

    return {
        "id": incident["id"],
        "alert_id": incident.get("alert_id"),
        "alert_title": alert["title"] if alert else None,
        "alert_event_type": alert.get("event_type") if alert else None,
        "alert_anomaly_score": float(alert["anomaly_score"]) if alert else None,
        "alert_is_anomalous": bool(alert["is_anomalous"]) if alert else None,
        "alert_parser_status": alert.get("parser_status") if alert else None,
        "alert_integration_ref": alert.get("integration_ref") if alert else None,
        "alert_lab_only": bool(alert.get("lab_only", False)) if alert else False,
        "alert_finding_metadata": alert_finding_metadata,
        "title": title,
        "priority": incident["priority"],
        "status": incident["status"],
        "notes": incident["notes"],
        "opened_at": incident["opened_at"],
        "updated_at": incident.get("updated_at") or incident["opened_at"],
        "closed_at": incident.get("closed_at"),
        "assigned_to_user_id": incident.get("assigned_to_user_id"),
        "assigned_to_name": user_lookup.get(incident.get("assigned_to_user_id")),
        "affected_asset": affected_asset,
        "source_tool": alert["source_tool"] if alert else None,
        "summary": summary,
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
    incident = next((item for item in _sorted_incidents() if item["id"] == incident_id), None)
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
    if any(incident.get("alert_id") == alert_id for incident in load_incident_records()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An incident already exists for this alert.",
        )

    alert = get_alert_by_id(alert_id)
    assignee_id = _validate_assignee(assigned_to_user_id)
    timestamp = utc_now()

    incident = {
        "id": next_prefixed_id("incident", (item["id"] for item in load_incident_records())),
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
    _persist_incident_record(incident)
    return _serialize_incident(incident)


def update_incident(incident_id: str, updates: dict) -> dict:
    incident = next((item for item in load_incident_records() if item["id"] == incident_id), None)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")

    memory_incident = next((item for item in DEMO_INCIDENTS if item["id"] == incident_id), None)
    target_incident = memory_incident if memory_incident is not None else incident

    if "assigned_to_user_id" in updates:
        target_incident["assigned_to_user_id"] = _validate_assignee(updates["assigned_to_user_id"])
        incident["assigned_to_user_id"] = target_incident["assigned_to_user_id"]

    if "priority" in updates and updates["priority"] is not None:
        target_incident["priority"] = updates["priority"]
        incident["priority"] = updates["priority"]

    if "notes" in updates and updates["notes"] is not None:
        target_incident["notes"] = updates["notes"]
        incident["notes"] = updates["notes"]

    if "status" in updates and updates["status"] is not None:
        target_incident["status"] = updates["status"]
        incident["status"] = updates["status"]
        if updates["status"] == IncidentStatus.RESOLVED:
            resolved_at = utc_now()
            target_incident["closed_at"] = resolved_at
            incident["closed_at"] = resolved_at
        else:
            target_incident["closed_at"] = None
            incident["closed_at"] = None

    target_incident["updated_at"] = utc_now()
    incident["updated_at"] = target_incident["updated_at"]
    _persist_incident_record(incident)
    return get_incident_by_id(incident_id)
