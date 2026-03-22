from app.core.enums import IntegrationTool
from app.services.alerts import load_alert_records
from app.services.logs import load_log_records
from app.services.mock_store import DEMO_INTEGRATIONS


def _augment_integration_status(integration: dict) -> dict:
    tool_name = integration["tool_name"]
    last_import_at = integration.get("last_import_at")
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
        "last_import_at": last_import_at,
        "last_import_message": integration.get("last_import_message"),
    }


def list_integrations() -> list[dict]:
    return [_augment_integration_status(integration) for integration in DEMO_INTEGRATIONS]


def get_integration_by_tool(tool_name: IntegrationTool | str) -> dict:
    integration = next((item for item in DEMO_INTEGRATIONS if item["tool_name"] == tool_name), None)
    if not integration:
        raise ValueError(f"Integration '{tool_name}' not found.")

    return integration


def get_augmented_integration_by_tool(tool_name: IntegrationTool | str) -> dict:
    return _augment_integration_status(get_integration_by_tool(tool_name))


def get_latest_alert_titles_for_tool(tool_name: IntegrationTool | str, limit: int = 3) -> list[str]:
    return [
        alert["title"]
        for alert in sorted(
            (item for item in load_alert_records() if item["source_tool"] == tool_name),
            key=lambda alert: alert["created_at"],
            reverse=True,
        )[:limit]
    ]
