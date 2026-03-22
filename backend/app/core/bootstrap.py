from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models.alert import Alert
from app.models.incident import Incident
from app.models.integration_import_state import IntegrationImportState
from app.models.integration_status import IntegrationStatus
from app.models.log_entry import LogEntry
from app.models.report import Report
from app.models.response_action import ResponseAction
from app.models.user import User
from app.models.virtual_machine import VirtualMachine
from app.services.anomaly import train_demo_anomaly_model
from app.services.mock_store import (
    DEMO_ALERTS,
    DEMO_INCIDENTS,
    DEMO_INTEGRATIONS,
    DEMO_LOGS,
    DEMO_REPORTS,
    DEMO_RESPONSE_ACTIONS,
    DEMO_USERS,
    DEMO_VIRTUAL_MACHINES,
)

logger = logging.getLogger(__name__)


def _sync_records(records: list[dict[str, Any]], factory: Callable[[dict[str, Any]], Any]) -> int:
    synced_count = 0

    with SessionLocal() as db:
        for record in records:
            db.merge(factory(record))
            synced_count += 1

        db.commit()

    return synced_count


def _seed_database_demo_records() -> dict[str, int]:
    init_db()

    summary = {
        "users": _sync_records(
            DEMO_USERS,
            lambda record: User(
                id=record["id"],
                full_name=record["full_name"],
                email=record["email"],
                password_hash=record["password_hash"],
                role=record["role"],
                is_active=record["is_active"],
                created_at=record["created_at"],
            ),
        ),
        "alerts": _sync_records(
            DEMO_ALERTS,
            lambda record: Alert(
                id=record["id"],
                title=record["title"],
                description=record["description"],
                source=record["source"],
                source_tool=record["source_tool"],
                severity=record["severity"],
                status=record["status"],
                confidence_score=record["confidence_score"],
                anomaly_score=record.get("anomaly_score", 0.0),
                is_anomalous=record.get("is_anomalous", False),
                anomaly_explanation=record.get("anomaly_explanation", ""),
                integration_ref=record.get("integration_ref"),
                finding_metadata=record.get("finding_metadata", {}),
                parser_status=record.get("parser_status"),
                lab_only=record.get("lab_only", False),
                created_at=record["created_at"],
            ),
        ),
        "incidents": _sync_records(
            DEMO_INCIDENTS,
            lambda record: Incident(
                id=record["id"],
                alert_id=record.get("alert_id"),
                assigned_to_user_id=record.get("assigned_to_user_id"),
                priority=record["priority"],
                status=record["status"],
                notes=record.get("notes", ""),
                opened_at=record["opened_at"],
                closed_at=record.get("closed_at"),
            ),
        ),
        "logs": _sync_records(
            DEMO_LOGS,
            lambda record: LogEntry(
                id=record["id"],
                source=record["source"],
                source_tool=record["source_tool"],
                severity=record["severity"],
                raw_log=record["raw_log"],
                normalized_log=record["normalized_log"],
                event_type=record["event_type"],
                integration_ref=record.get("integration_ref"),
                finding_metadata=record.get("finding_metadata", {}),
                parser_status=record.get("parser_status"),
                lab_only=record.get("lab_only", False),
                created_at=record["created_at"],
            ),
        ),
        "reports": _sync_records(
            DEMO_REPORTS,
            lambda record: Report(
                id=record["id"],
                title=record["title"],
                report_type=record["report_type"],
                generated_by_user_id=record.get("generated_by_user_id"),
                content_json=record["content_json"],
                status=record["status"],
                created_at=record["created_at"],
            ),
        ),
        "integrations": _sync_records(
            DEMO_INTEGRATIONS,
            lambda record: IntegrationStatus(
                id=record["id"],
                tool_name=record["tool_name"],
                status=record["status"],
                last_sync_at=record["last_sync_at"],
                notes=record.get("notes", ""),
            ),
        ),
        "integration_import_states": _sync_records(
            DEMO_INTEGRATIONS,
            lambda record: IntegrationImportState(
                tool_name=record["tool_name"],
                last_import_at=record.get("last_import_at"),
                last_import_message=record.get("last_import_message"),
            ),
        ),
        "response_actions": _sync_records(
            DEMO_RESPONSE_ACTIONS,
            lambda record: ResponseAction(
                id=record["id"],
                alert_id=record["alert_id"],
                action_type=record["action_type"],
                status=record["status"],
                execution_mode=record["execution_mode"],
                target_label=record.get("target_label"),
                notes=record.get("notes", ""),
                result_summary=record.get("result_summary", ""),
                performed_by_user_id=record.get("performed_by_user_id"),
                incident_id=record.get("incident_id"),
                created_at=record["created_at"],
            ),
        ),
        "virtual_machines": _sync_records(
            DEMO_VIRTUAL_MACHINES,
            lambda record: VirtualMachine(
                id=record["id"],
                vm_name=record["vm_name"],
                role=record["role"],
                os_type=record["os_type"],
                ip_address=record["ip_address"],
                status=record["status"],
                notes=record.get("notes", ""),
            ),
        ),
    }

    return summary


def bootstrap_demo_environment() -> dict[str, Any]:
    summary: dict[str, Any] = {
        "database_seeded": False,
        "database_counts": {},
        "anomaly_model_ready": False,
    }

    try:
        train_demo_anomaly_model(force_retrain=False)
        summary["anomaly_model_ready"] = True
    except Exception as error:  # pragma: no cover - startup safety net
        logger.warning("Demo anomaly model bootstrap skipped: %s", error)

    try:
        summary["database_counts"] = _seed_database_demo_records()
        summary["database_seeded"] = True
    except SQLAlchemyError as error:
        logger.warning("Database bootstrap skipped because the database is not ready: %s", error)
    except Exception as error:  # pragma: no cover - startup safety net
        logger.warning("Database bootstrap skipped because of an unexpected error: %s", error)

    return summary
