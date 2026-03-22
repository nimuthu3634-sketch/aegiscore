from __future__ import annotations

from sqlalchemy import select

from app.core.enums import IntegrationHealth, IntegrationTool
from app.models.integration_import_state import IntegrationImportState
from app.models.integration_status import IntegrationStatus
from app.services.alerts import load_alert_records
from app.services.logs import load_log_records
from app.services.mock_store import DEMO_INTEGRATIONS
from app.services.persistence import run_with_optional_db
from app.utils.time import ensure_utc


def _integration_from_model(integration: IntegrationStatus) -> dict:
    return {
        "id": integration.id,
        "tool_name": integration.tool_name,
        "status": integration.status,
        "last_sync_at": ensure_utc(integration.last_sync_at),
        "notes": integration.notes,
    }


def _integration_import_state_from_model(import_state: IntegrationImportState) -> dict:
    return {
        "tool_name": import_state.tool_name,
        "last_import_at": ensure_utc(import_state.last_import_at),
        "last_import_message": import_state.last_import_message,
    }


def _load_persisted_integrations() -> list[dict]:
    def operation(db) -> list[dict]:
        integrations = db.scalars(select(IntegrationStatus)).all()
        return [_integration_from_model(integration) for integration in integrations]

    return run_with_optional_db(operation, lambda: [])


def _load_persisted_import_states() -> list[dict]:
    def operation(db) -> list[dict]:
        import_states = db.scalars(select(IntegrationImportState)).all()
        return [
            _integration_import_state_from_model(import_state)
            for import_state in import_states
        ]

    return run_with_optional_db(operation, lambda: [])


def load_integration_records() -> list[dict]:
    merged_records = {
        integration["tool_name"]: dict(integration)
        for integration in DEMO_INTEGRATIONS
    }

    for persisted_integration in _load_persisted_integrations():
        tool_name = persisted_integration["tool_name"]
        if tool_name in merged_records:
            merged_records[tool_name] = {
                **merged_records[tool_name],
                **persisted_integration,
            }
        else:
            merged_records[tool_name] = persisted_integration

    for import_state in _load_persisted_import_states():
        tool_name = import_state["tool_name"]
        if tool_name in merged_records:
            merged_records[tool_name] = {
                **merged_records[tool_name],
                **import_state,
            }

    return list(merged_records.values())


def _augment_integration_status(integration: dict) -> dict:
    tool_name = integration["tool_name"]
    imported_alert_count = sum(
        1 for alert in load_alert_records() if alert["source_tool"] == tool_name
    )
    imported_log_count = sum(
        1 for log_entry in load_log_records() if log_entry["source_tool"] == tool_name
    )

    return {
        **integration,
        "imported_alert_count": imported_alert_count,
        "imported_log_count": imported_log_count,
        "last_import_at": integration.get("last_import_at"),
        "last_import_message": integration.get("last_import_message"),
    }


def _memory_integration(tool_name: IntegrationTool | str) -> dict | None:
    return next((item for item in DEMO_INTEGRATIONS if item["tool_name"] == tool_name), None)


def list_integrations() -> list[dict]:
    return [_augment_integration_status(integration) for integration in load_integration_records()]


def get_integration_by_tool(tool_name: IntegrationTool | str) -> dict:
    integration = next(
        (item for item in load_integration_records() if item["tool_name"] == tool_name),
        None,
    )
    if not integration:
        raise ValueError(f"Integration '{tool_name}' not found.")

    return integration


def get_augmented_integration_by_tool(tool_name: IntegrationTool | str) -> dict:
    return _augment_integration_status(get_integration_by_tool(tool_name))


def update_integration_runtime(
    tool_name: IntegrationTool | str,
    *,
    status: IntegrationHealth,
    last_sync_at,
    notes: str,
    last_import_at=None,
    last_import_message: str | None = None,
) -> dict:
    memory_integration = _memory_integration(tool_name)
    integration_record = memory_integration or get_integration_by_tool(tool_name)

    if memory_integration is not None:
        memory_integration["status"] = status
        memory_integration["last_sync_at"] = last_sync_at
        memory_integration["notes"] = notes
        memory_integration["last_import_at"] = last_import_at
        memory_integration["last_import_message"] = last_import_message

    def operation(db) -> None:
        db.merge(
            IntegrationStatus(
                id=integration_record["id"],
                tool_name=integration_record["tool_name"],
                status=status,
                last_sync_at=last_sync_at,
                notes=notes,
            )
        )
        db.merge(
            IntegrationImportState(
                tool_name=integration_record["tool_name"],
                last_import_at=last_import_at,
                last_import_message=last_import_message,
            )
        )
        db.commit()

    run_with_optional_db(operation, lambda: None)
    return get_augmented_integration_by_tool(tool_name)


def get_latest_alert_titles_for_tool(tool_name: IntegrationTool | str, limit: int = 3) -> list[str]:
    return [
        alert["title"]
        for alert in sorted(
            (item for item in load_alert_records() if item["source_tool"] == tool_name),
            key=lambda alert: alert["created_at"],
            reverse=True,
        )[:limit]
    ]
