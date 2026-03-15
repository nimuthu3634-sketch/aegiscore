from fastapi import HTTPException, status

from app.services.mock_store import DEMO_LOGS
from app.utils.log_normalization import normalize_log_payload


def _sorted_logs() -> list[dict]:
    return sorted(DEMO_LOGS, key=lambda entry: entry["created_at"], reverse=True)


def list_logs() -> dict:
    logs = _sorted_logs()
    return {"items": logs, "total_items": len(logs)}


def get_log_by_id(log_id: str) -> dict:
    log_entry = next((item for item in DEMO_LOGS if item["id"] == log_id), None)
    if not log_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log entry not found.")

    return log_entry


def ingest_log(payload: dict) -> dict:
    normalized_entry = normalize_log_payload(payload)
    log_record = {
        "id": f"log-{len(DEMO_LOGS) + 1:03d}",
        **normalized_entry,
    }
    DEMO_LOGS.append(log_record)
    return log_record
