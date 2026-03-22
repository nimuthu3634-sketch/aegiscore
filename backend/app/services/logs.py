from fastapi import HTTPException, status
from sqlalchemy import select

from app.models.log_entry import LogEntry
from app.services.mock_store import DEMO_LOGS
from app.services.persistence import run_with_optional_db
from app.services.record_ids import next_prefixed_id
from app.utils.log_normalization import normalize_log_payload
from app.utils.time import ensure_utc


def _log_from_model(log_entry: LogEntry) -> dict:
    return {
        "id": log_entry.id,
        "source": log_entry.source,
        "source_tool": log_entry.source_tool,
        "raw_log": log_entry.raw_log,
        "normalized_log": log_entry.normalized_log,
        "event_type": log_entry.event_type,
        "severity": log_entry.severity,
        "integration_ref": log_entry.integration_ref,
        "finding_metadata": log_entry.finding_metadata or {},
        "parser_status": log_entry.parser_status,
        "lab_only": log_entry.lab_only,
        "created_at": ensure_utc(log_entry.created_at),
    }


def _load_persisted_logs() -> list[dict]:
    def operation(db) -> list[dict]:
        log_entries = db.scalars(select(LogEntry).order_by(LogEntry.created_at.desc())).all()
        return [_log_from_model(log_entry) for log_entry in log_entries]

    return run_with_optional_db(operation, lambda: [])


def load_log_records() -> list[dict]:
    merged_logs = {log_entry["id"]: dict(log_entry) for log_entry in DEMO_LOGS}

    for persisted_log in _load_persisted_logs():
        if persisted_log["id"] in merged_logs:
            merged_logs[persisted_log["id"]] = {
                **merged_logs[persisted_log["id"]],
                **persisted_log,
            }
        else:
            merged_logs[persisted_log["id"]] = persisted_log

    return list(merged_logs.values())


def _sorted_logs() -> list[dict]:
    return sorted(load_log_records(), key=lambda entry: entry["created_at"], reverse=True)


def _persist_log_record(log_record: dict) -> None:
    def operation(db) -> None:
        db.merge(
            LogEntry(
                id=log_record["id"],
                source=log_record["source"],
                source_tool=log_record["source_tool"],
                severity=log_record["severity"],
                raw_log=log_record["raw_log"],
                normalized_log=log_record["normalized_log"],
                event_type=log_record["event_type"],
                integration_ref=log_record.get("integration_ref"),
                finding_metadata=log_record.get("finding_metadata", {}),
                parser_status=log_record.get("parser_status"),
                lab_only=log_record.get("lab_only", False),
                created_at=log_record["created_at"],
            )
        )
        db.commit()

    run_with_optional_db(operation, lambda: None)


def list_logs() -> dict:
    logs = _sorted_logs()
    return {"items": logs, "total_items": len(logs)}


def get_log_by_id(log_id: str) -> dict:
    log_entry = next((item for item in _sorted_logs() if item["id"] == log_id), None)
    if not log_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log entry not found.")

    return log_entry


def create_log_record(payload: dict, extra_fields: dict | None = None) -> dict:
    normalized_entry = normalize_log_payload(payload)
    log_record = {
        "id": next_prefixed_id("log", (log_entry["id"] for log_entry in load_log_records())),
        **normalized_entry,
    }

    if extra_fields:
        log_record.update(extra_fields)

    DEMO_LOGS.append(log_record)
    _persist_log_record(log_record)
    return log_record


def ingest_log(payload: dict) -> dict:
    return create_log_record(payload)
