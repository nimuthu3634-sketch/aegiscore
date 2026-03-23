from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import select

from app.services.anomaly import apply_anomaly_scoring, ensure_demo_alerts_scored
from app.core.enums import AlertSeverity, AlertStatus, IntegrationTool
from app.models.alert import Alert
from app.services.logs import load_log_records
from app.services.mock_store import DEMO_ALERTS
from app.services.persistence import run_with_optional_db
from app.services.record_ids import next_prefixed_id
from app.services.websocket import broadcast_alert_created
from app.utils.time import ensure_utc, utc_now


def _alert_from_model(alert: Alert) -> dict:
    return {
        "id": alert.id,
        "title": alert.title,
        "description": alert.description,
        "source": alert.source,
        "source_tool": alert.source_tool,
        "severity": alert.severity,
        "status": alert.status,
        "confidence_score": alert.confidence_score,
        "anomaly_score": alert.anomaly_score,
        "is_anomalous": alert.is_anomalous,
        "anomaly_explanation": alert.anomaly_explanation,
        "integration_ref": alert.integration_ref,
        "finding_metadata": alert.finding_metadata or {},
        "parser_status": alert.parser_status,
        "lab_only": alert.lab_only,
        "created_at": ensure_utc(alert.created_at),
    }


def _normalize_event_type(value: str | None) -> str | None:
    if value is None:
        return None

    normalized_value = value.strip().lower().replace(" ", "_")
    return normalized_value or None


def _resolve_alert_event_type(alert_record: dict) -> str:
    explicit_event_type = _normalize_event_type(alert_record.get("event_type"))
    if explicit_event_type:
        return explicit_event_type

    finding_metadata = (
        alert_record.get("finding_metadata", {})
        if isinstance(alert_record.get("finding_metadata"), dict)
        else {}
    )
    metadata_event_type = _normalize_event_type(finding_metadata.get("event_type"))
    if metadata_event_type:
        return metadata_event_type

    integration_ref = alert_record.get("integration_ref")
    if integration_ref:
        related_log = next(
            (
                log_entry
                for log_entry in load_log_records()
                if log_entry.get("integration_ref") == integration_ref
            ),
            None,
        )
        if related_log and related_log.get("event_type"):
            return _normalize_event_type(related_log["event_type"]) or "security_alert"

    candidate_logs = [
        log_entry
        for log_entry in load_log_records()
        if log_entry.get("source") == alert_record.get("source")
        and log_entry.get("source_tool") == alert_record.get("source_tool")
    ]
    if candidate_logs:
        closest_log = min(
            candidate_logs,
            key=lambda log_entry: abs(
                (log_entry["created_at"] - alert_record["created_at"]).total_seconds()
            ),
        )
        return _normalize_event_type(closest_log.get("event_type")) or "security_alert"

    return "security_alert"


def _enrich_alert_record(alert_record: dict) -> dict:
    enriched_record = dict(alert_record)
    enriched_record["finding_metadata"] = (
        alert_record.get("finding_metadata", {})
        if isinstance(alert_record.get("finding_metadata"), dict)
        else {}
    )
    enriched_record["parser_status"] = alert_record.get("parser_status")
    enriched_record["lab_only"] = bool(alert_record.get("lab_only", False))
    enriched_record["event_type"] = _resolve_alert_event_type(alert_record)
    return enriched_record


def _load_persisted_alerts() -> list[dict]:
    def operation(db) -> list[dict]:
        alerts = db.scalars(select(Alert).order_by(Alert.created_at.desc())).all()
        return [_alert_from_model(alert) for alert in alerts]

    return run_with_optional_db(operation, lambda: [])


def load_alert_records() -> list[dict]:
    ensure_demo_alerts_scored()
    merged_alerts = {alert["id"]: dict(alert) for alert in DEMO_ALERTS}

    for persisted_alert in _load_persisted_alerts():
        if persisted_alert["id"] in merged_alerts:
            merged_alerts[persisted_alert["id"]] = {
                **merged_alerts[persisted_alert["id"]],
                **persisted_alert,
            }
        else:
            merged_alerts[persisted_alert["id"]] = persisted_alert

    return [_enrich_alert_record(alert) for alert in merged_alerts.values()]


def _sorted_alerts() -> list[dict]:
    return sorted(load_alert_records(), key=lambda alert: alert["created_at"], reverse=True)


def _persist_alert_record(alert_record: dict) -> None:
    def operation(db) -> None:
        db.merge(
            Alert(
                id=alert_record["id"],
                title=alert_record["title"],
                description=alert_record["description"],
                source=alert_record["source"],
                source_tool=alert_record["source_tool"],
                severity=alert_record["severity"],
                status=alert_record["status"],
                confidence_score=alert_record["confidence_score"],
                anomaly_score=alert_record["anomaly_score"],
                is_anomalous=alert_record["is_anomalous"],
                anomaly_explanation=alert_record["anomaly_explanation"],
                integration_ref=alert_record.get("integration_ref"),
                finding_metadata=alert_record.get("finding_metadata", {}),
                parser_status=alert_record.get("parser_status"),
                lab_only=alert_record.get("lab_only", False),
                created_at=alert_record["created_at"],
            )
        )
        db.commit()

    run_with_optional_db(operation, lambda: None)


def _matches_filters(
    alert: dict,
    severity: AlertSeverity | None,
    status_filter: AlertStatus | None,
    source_tool: IntegrationTool | None,
    event_type: str | None,
    search: str | None,
) -> bool:
    if severity and alert["severity"] != severity:
        return False

    if status_filter and alert["status"] != status_filter:
        return False

    if source_tool and alert["source_tool"] != source_tool:
        return False

    if event_type and alert.get("event_type") != _normalize_event_type(event_type):
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
    event_type: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    filtered_alerts = [
        alert
        for alert in _sorted_alerts()
        if _matches_filters(alert, severity, status_filter, source_tool, event_type, search)
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
    alert = next((item for item in _sorted_alerts() if item["id"] == alert_id), None)
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
        "id": next_prefixed_id("alert", (alert["id"] for alert in load_alert_records())),
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

    apply_anomaly_scoring(alert_record, reference_alerts=load_alert_records())
    alert_record = _enrich_alert_record(alert_record)
    DEMO_ALERTS.append(alert_record)
    _persist_alert_record(alert_record)
    from app.services.response_actions import run_automatic_response_workflow

    run_automatic_response_workflow(alert_record["id"])
    broadcast_alert_created(alert_record)
    return alert_record


def update_alert_status(alert_id: str, alert_status: AlertStatus) -> dict:
    alert = get_alert_by_id(alert_id)

    memory_alert = next((item for item in DEMO_ALERTS if item["id"] == alert_id), None)
    if memory_alert:
        memory_alert["status"] = alert_status

    alert["status"] = alert_status
    _persist_alert_record(alert)
    return get_alert_by_id(alert_id)
