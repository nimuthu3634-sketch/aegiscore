from __future__ import annotations

from sqlalchemy import select

from fastapi import HTTPException, status

from app.core.enums import (
    AlertStatus,
    ResponseActionMode,
    ResponseActionStatus,
    ResponseActionType,
)
from app.models.response_action import ResponseAction
from app.services.alerts import get_alert_by_id, update_alert_status
from app.services.incidents import create_incident, load_incident_records
from app.services.logs import load_log_records
from app.services.mock_store import (
    DEMO_BLOCKED_IPS,
    DEMO_DISABLED_ACCOUNTS,
    DEMO_ISOLATED_ASSETS,
    DEMO_RESPONSE_ACTIONS,
)
from app.services.persistence import run_with_optional_db
from app.services.record_ids import next_prefixed_id
from app.services.users import get_user_by_id
from app.utils.time import ensure_utc, utc_now

ANALYST_ACTOR_NAME = "SOC Analyst"


def _first_present(*values):
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return str(value)

    return None


def _response_action_from_model(action: ResponseAction) -> dict:
    return {
        "id": action.id,
        "alert_id": action.alert_id,
        "action_type": action.action_type,
        "status": action.status,
        "execution_mode": ResponseActionMode.MANUAL,
        "target_label": action.target_label,
        "notes": action.notes,
        "result_summary": action.result_summary,
        "performed_by_user_id": action.performed_by_user_id,
        "incident_id": action.incident_id,
        "created_at": ensure_utc(action.created_at),
    }


def _load_persisted_response_actions() -> list[dict]:
    def operation(db) -> list[dict]:
        actions = db.scalars(select(ResponseAction)).all()
        return [_response_action_from_model(action) for action in actions]

    return run_with_optional_db(operation, lambda: [])


def load_response_action_records() -> list[dict]:
    merged_actions = {
        action["id"]: dict(action)
        for action in DEMO_RESPONSE_ACTIONS
    }

    for persisted_action in _load_persisted_response_actions():
        if persisted_action["id"] in merged_actions:
            merged_actions[persisted_action["id"]] = {
                **merged_actions[persisted_action["id"]],
                **persisted_action,
            }
        else:
            merged_actions[persisted_action["id"]] = persisted_action

    filtered_actions: list[dict] = []
    for action in merged_actions.values():
        try:
            get_alert_by_id(action["alert_id"])
        except HTTPException:
            continue

        filtered_actions.append(
            {
                **action,
                "execution_mode": ResponseActionMode.MANUAL,
            }
        )

    return filtered_actions


def _persist_response_action(action_record: dict) -> None:
    def operation(db) -> None:
        db.merge(
            ResponseAction(
                id=action_record["id"],
                alert_id=action_record["alert_id"],
                action_type=action_record["action_type"],
                status=action_record["status"],
                execution_mode=action_record["execution_mode"],
                target_label=action_record.get("target_label"),
                notes=action_record.get("notes", ""),
                result_summary=action_record.get("result_summary", ""),
                performed_by_user_id=action_record.get("performed_by_user_id"),
                incident_id=action_record.get("incident_id"),
                created_at=action_record["created_at"],
            )
        )
        db.commit()

    run_with_optional_db(operation, lambda: None)


def _related_log_for_alert(alert: dict) -> dict | None:
    integration_ref = alert.get("integration_ref")
    if integration_ref:
        return next(
            (log_entry for log_entry in load_log_records() if log_entry.get("integration_ref") == integration_ref),
            None,
        )

    candidates = [
        log_entry
        for log_entry in load_log_records()
        if log_entry.get("source") == alert.get("source")
        and log_entry.get("source_tool") == alert.get("source_tool")
    ]
    if not candidates:
        return None

    return min(
        candidates,
        key=lambda log_entry: abs(
            (log_entry["created_at"] - alert["created_at"]).total_seconds()
        ),
    )


def _extract_response_targets(alert: dict) -> dict:
    related_log = _related_log_for_alert(alert)
    normalized_log = related_log.get("normalized_log", {}) if related_log else {}
    raw_log = related_log.get("raw_log", {}) if related_log else {}
    observables = normalized_log.get("observables", {}) if isinstance(normalized_log, dict) else {}
    finding_metadata = alert.get("finding_metadata", {})
    if not isinstance(finding_metadata, dict):
        finding_metadata = {}

    return {
        "event_type": (
            related_log.get("event_type")
            if related_log
            else finding_metadata.get("event_type") or "security_alert"
        ),
        "source_ip": _first_present(
            observables.get("source_ip"),
            raw_log.get("source_ip"),
            raw_log.get("src_ip"),
            finding_metadata.get("source_ip"),
        ),
        "account": _first_present(
            observables.get("actor"),
            raw_log.get("username"),
            raw_log.get("user"),
            raw_log.get("account"),
            finding_metadata.get("username"),
        ),
        "asset": _first_present(
            alert.get("source"),
            raw_log.get("host"),
            raw_log.get("asset"),
            raw_log.get("target_system"),
            finding_metadata.get("host"),
            finding_metadata.get("target_system"),
        ),
    }


def _find_existing_incident(alert_id: str) -> dict | None:
    return next((incident for incident in load_incident_records() if incident.get("alert_id") == alert_id), None)


def _find_user_name(user_id: str | None) -> str | None:
    if user_id is None:
        return None

    user = get_user_by_id(user_id)
    return user["full_name"] if user else None


def _resolve_actor(actor: dict | None, execution_mode: ResponseActionMode) -> tuple[str | None, str]:
    if actor is None:
        return None, ANALYST_ACTOR_NAME

    return actor.get("id"), actor.get("full_name") or _find_user_name(actor.get("id")) or ANALYST_ACTOR_NAME


def _serialize_action(action_record: dict) -> dict:
    performed_by_user_id = action_record.get("performed_by_user_id")
    performed_by_name = action_record.get("performed_by_name") or _find_user_name(performed_by_user_id)
    return {
        **action_record,
        "execution_mode": ResponseActionMode.MANUAL,
        "performed_by_name": performed_by_name or ANALYST_ACTOR_NAME,
    }


def _record_action(
    *,
    alert_id: str,
    action_type: ResponseActionType,
    action_status: ResponseActionStatus,
    execution_mode: ResponseActionMode,
    target_label: str | None,
    notes: str,
    result_summary: str,
    actor: dict | None,
    incident_id: str | None = None,
) -> dict:
    performed_by_user_id, performed_by_name = _resolve_actor(actor, execution_mode)
    action_record = {
        "id": next_prefixed_id(
            "response",
            (action["id"] for action in load_response_action_records()),
        ),
        "alert_id": alert_id,
        "action_type": action_type,
        "status": action_status,
        "execution_mode": ResponseActionMode.MANUAL,
        "target_label": target_label,
        "notes": notes,
        "result_summary": result_summary,
        "performed_by_user_id": performed_by_user_id,
        "performed_by_name": performed_by_name,
        "incident_id": incident_id,
        "created_at": utc_now(),
    }
    DEMO_RESPONSE_ACTIONS.insert(0, action_record)
    _persist_response_action(action_record)
    return _serialize_action(action_record)


def _completed_action_targets(action_type: ResponseActionType) -> set[str]:
    return {
        str(action["target_label"])
        for action in load_response_action_records()
        if action["action_type"] == action_type
        and action["status"] == ResponseActionStatus.COMPLETED
        and action.get("target_label")
    }


def _is_ip_blocked(source_ip: str | None) -> bool:
    if source_ip is None:
        return False

    return source_ip in _completed_action_targets(ResponseActionType.BLOCK_SOURCE_IP) or any(
        record["source_ip"] == source_ip for record in DEMO_BLOCKED_IPS
    )


def _is_asset_isolated(asset: str | None) -> bool:
    if asset is None:
        return False

    return asset in _completed_action_targets(ResponseActionType.ISOLATE_ASSET) or any(
        record["asset"] == asset for record in DEMO_ISOLATED_ASSETS
    )


def _is_account_disabled(account: str | None) -> bool:
    if account is None:
        return False

    return account in _completed_action_targets(ResponseActionType.DISABLE_ACCOUNT) or any(
        record["account"] == account for record in DEMO_DISABLED_ACCOUNTS
    )


def _build_suggestions(alert: dict) -> list[dict]:
    targets = _extract_response_targets(alert)
    incident = _find_existing_incident(alert["id"])
    suggestions = [
        {
            "action_type": ResponseActionType.CREATE_INCIDENT,
            "label": "Create incident",
            "description": (
                f"Incident {incident['id']} already exists for this alert."
                if incident
                else "Escalate this alert into the incident workflow for assignment and tracking."
            ),
            "target_label": incident["id"] if incident else targets["asset"],
            "available": incident is None,
        },
        {
            "action_type": ResponseActionType.MARK_INVESTIGATING,
            "label": "Move to investigating",
            "description": (
                "This alert is already under investigation."
                if alert["status"] == AlertStatus.INVESTIGATING
                else "Move the alert into the active investigation state."
            ),
            "target_label": alert["status"].value.replace("_", " "),
            "available": alert["status"] not in {AlertStatus.INVESTIGATING, AlertStatus.RESOLVED},
        },
        {
            "action_type": ResponseActionType.ISOLATE_ASSET,
            "label": "Isolate asset",
            "description": (
                "A lab-only isolation record already exists for this asset."
                if _is_asset_isolated(targets["asset"])
                else "Record a simulated host isolation action for the affected asset."
            ),
            "target_label": targets["asset"],
            "available": bool(targets["asset"]) and not _is_asset_isolated(targets["asset"]),
        },
    ]

    if targets["source_ip"]:
        suggestions.append(
            {
                "action_type": ResponseActionType.BLOCK_SOURCE_IP,
                "label": "Block source IP",
                "description": (
                    "This source IP is already present in the simulated lab blocklist."
                    if _is_ip_blocked(targets["source_ip"])
                    else "Add the source IP to the lab-only simulated blocklist."
                ),
                "target_label": targets["source_ip"],
                "available": not _is_ip_blocked(targets["source_ip"]),
            }
        )

    if targets["account"] and targets["event_type"] in {
        "authentication",
        "credential_assessment",
        "privilege_change",
        "user_account",
    }:
        suggestions.append(
            {
                "action_type": ResponseActionType.DISABLE_ACCOUNT,
                "label": "Disable account",
                "description": (
                    "A lab-only disable action already exists for this account."
                    if _is_account_disabled(targets["account"])
                    else "Record a simulated account disable action for the affected account."
                ),
                "target_label": targets["account"],
                "available": not _is_account_disabled(targets["account"]),
            }
        )

    return suggestions


def list_response_actions(alert_id: str) -> dict:
    alert = get_alert_by_id(alert_id)
    history = sorted(
        (action for action in load_response_action_records() if action["alert_id"] == alert_id),
        key=lambda action: action["created_at"],
        reverse=True,
    )

    return {
        "items": [_serialize_action(action) for action in history],
        "recommended_actions": _build_suggestions(alert),
    }


def execute_response_action(
    *,
    alert_id: str,
    action_type: ResponseActionType,
    actor: dict | None,
    notes: str = "",
    execution_mode: ResponseActionMode = ResponseActionMode.MANUAL,
) -> dict:
    alert = get_alert_by_id(alert_id)
    targets = _extract_response_targets(alert)
    clean_notes = notes.strip()

    if action_type == ResponseActionType.CREATE_INCIDENT:
        existing_incident = _find_existing_incident(alert_id)
        if existing_incident:
            return _record_action(
                alert_id=alert_id,
                action_type=action_type,
                action_status=ResponseActionStatus.SKIPPED,
                execution_mode=execution_mode,
                target_label=existing_incident["id"],
                notes=clean_notes or "Incident creation skipped because a linked incident already exists.",
                result_summary=f"Incident {existing_incident['id']} already exists for this alert.",
                actor=actor,
                incident_id=existing_incident["id"],
            )

        incident = create_incident(
            alert_id=alert_id,
            notes=clean_notes or "Incident created through the response action workflow.",
        )
        return _record_action(
            alert_id=alert_id,
            action_type=action_type,
            action_status=ResponseActionStatus.COMPLETED,
            execution_mode=execution_mode,
            target_label=incident["id"],
            notes=clean_notes or "Incident created through the response action workflow.",
            result_summary=f"Incident {incident['id']} was opened for {alert['source']}.",
            actor=actor,
            incident_id=incident["id"],
        )

    if action_type == ResponseActionType.MARK_INVESTIGATING:
        if alert["status"] == AlertStatus.INVESTIGATING:
            return _record_action(
                alert_id=alert_id,
                action_type=action_type,
                action_status=ResponseActionStatus.SKIPPED,
                execution_mode=execution_mode,
                target_label=alert["status"].value,
                notes=clean_notes or "Alert is already marked as investigating.",
                result_summary="No change was applied because the alert is already under investigation.",
                actor=actor,
            )

        if alert["status"] == AlertStatus.RESOLVED:
            return _record_action(
                alert_id=alert_id,
                action_type=action_type,
                action_status=ResponseActionStatus.SKIPPED,
                execution_mode=execution_mode,
                target_label=alert["status"].value,
                notes=clean_notes or "Resolved alerts are not moved back into investigation automatically.",
                result_summary="No change was applied because the alert is already resolved.",
                actor=actor,
            )

        alert = update_alert_status(alert_id, AlertStatus.INVESTIGATING)
        return _record_action(
            alert_id=alert_id,
            action_type=action_type,
            action_status=ResponseActionStatus.COMPLETED,
            execution_mode=execution_mode,
            target_label=alert["status"].value,
            notes=clean_notes or "Alert moved into the active investigation state.",
            result_summary="Alert status updated to investigating.",
            actor=actor,
        )

    if action_type == ResponseActionType.BLOCK_SOURCE_IP:
        source_ip = targets["source_ip"]
        if not source_ip:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No source IP is available for this alert.",
            )

        if _is_ip_blocked(source_ip):
            return _record_action(
                alert_id=alert_id,
                action_type=action_type,
                action_status=ResponseActionStatus.SKIPPED,
                execution_mode=execution_mode,
                target_label=source_ip,
                notes=clean_notes or "Source IP was already present in the simulated blocklist.",
                result_summary=f"Source IP {source_ip} is already present in the simulated blocklist.",
                actor=actor,
            )

        DEMO_BLOCKED_IPS.append(
            {
                "source_ip": source_ip,
                "alert_id": alert_id,
                "created_at": utc_now(),
                "created_by_user_id": actor.get("id") if actor else None,
                "execution_mode": execution_mode,
            }
        )
        if alert["status"] != AlertStatus.RESOLVED:
            update_alert_status(alert_id, AlertStatus.INVESTIGATING)

        return _record_action(
            alert_id=alert_id,
            action_type=action_type,
            action_status=ResponseActionStatus.COMPLETED,
            execution_mode=execution_mode,
            target_label=source_ip,
            notes=clean_notes or "Source IP added to the lab-only simulated blocklist.",
            result_summary=f"Source IP {source_ip} was added to the simulated lab blocklist.",
            actor=actor,
        )

    if action_type == ResponseActionType.DISABLE_ACCOUNT:
        account = targets["account"]
        if not account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No account identifier is available for this alert.",
            )

        if _is_account_disabled(account):
            return _record_action(
                alert_id=alert_id,
                action_type=action_type,
                action_status=ResponseActionStatus.SKIPPED,
                execution_mode=execution_mode,
                target_label=account,
                notes=clean_notes or "Account already has a simulated disable record.",
                result_summary=f"Account {account} already has a simulated disable record.",
                actor=actor,
            )

        DEMO_DISABLED_ACCOUNTS.append(
            {
                "account": account,
                "alert_id": alert_id,
                "created_at": utc_now(),
                "created_by_user_id": actor.get("id") if actor else None,
                "execution_mode": execution_mode,
            }
        )
        if alert["status"] != AlertStatus.RESOLVED:
            update_alert_status(alert_id, AlertStatus.INVESTIGATING)

        return _record_action(
            alert_id=alert_id,
            action_type=action_type,
            action_status=ResponseActionStatus.COMPLETED,
            execution_mode=execution_mode,
            target_label=account,
            notes=clean_notes or "Account disable action recorded for the lab workflow.",
            result_summary=f"Account {account} was recorded as disabled in the simulated response log.",
            actor=actor,
        )

    if action_type == ResponseActionType.ISOLATE_ASSET:
        asset = targets["asset"]
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No asset identifier is available for this alert.",
            )

        if _is_asset_isolated(asset):
            return _record_action(
                alert_id=alert_id,
                action_type=action_type,
                action_status=ResponseActionStatus.SKIPPED,
                execution_mode=execution_mode,
                target_label=asset,
                notes=clean_notes or "Asset already has a simulated isolation record.",
                result_summary=f"Asset {asset} already has a simulated isolation record.",
                actor=actor,
            )

        DEMO_ISOLATED_ASSETS.append(
            {
                "asset": asset,
                "alert_id": alert_id,
                "created_at": utc_now(),
                "created_by_user_id": actor.get("id") if actor else None,
                "execution_mode": execution_mode,
            }
        )
        if alert["status"] != AlertStatus.RESOLVED:
            update_alert_status(alert_id, AlertStatus.INVESTIGATING)

        return _record_action(
            alert_id=alert_id,
            action_type=action_type,
            action_status=ResponseActionStatus.COMPLETED,
            execution_mode=execution_mode,
            target_label=asset,
            notes=clean_notes or "Asset isolation recorded as a simulated lab response.",
            result_summary=f"Asset {asset} was recorded as isolated in the lab-only response log.",
            actor=actor,
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported response action.",
    )
