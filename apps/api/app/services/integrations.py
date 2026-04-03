from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.ingestion.normalization import LAB_ONLY_IMPORT_SOURCES, SYNC_CAPABLE_SOURCES
from app.ingestion.parsers import parse_telemetry
from app.models.entities import Alert, Integration, IntegrationHealth, IntegrationRun, LogEntry, User
from app.schemas.domain import IntegrationConfigUpdate
from app.services.audit import record_audit
from app.services.domain import broadcast_alert_event, create_alert, ensure_asset


DEFAULT_SYNC_CONFIG = {
    "endpoint_url": None,
    "auth_type": "none",
    "username": None,
    "password": None,
    "api_token": None,
    "verify_tls": True,
    "timeout_seconds": 15,
    "lookback_minutes": 60,
    "request_headers": {},
    "query_params": {},
}


@dataclass(slots=True)
class IngestionSummary:
    integration: str
    run_id: str
    mode: str
    status: str
    alerts_created: int = 0
    alerts_updated: int = 0
    logs_created: int = 0
    assets_touched: int = 0
    incident_candidates: int = 0
    normalized_records: int = 0
    input_format: str | None = None
    imported_lab_data: bool = False
    created_alerts: list[Alert] = field(default_factory=list)


def _integration_or_404(db: Session, slug: str) -> Integration:
    integration = db.query(Integration).filter(Integration.slug == slug).one_or_none()
    if integration is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")
    return integration


def _is_sync_capable(slug: str) -> bool:
    return slug in SYNC_CAPABLE_SOURCES


def _default_config_for(slug: str) -> dict[str, Any]:
    if _is_sync_capable(slug):
        return dict(DEFAULT_SYNC_CONFIG)
    return {"import_only": True}


def _merge_config(slug: str, config: dict[str, Any] | None) -> dict[str, Any]:
    merged = _default_config_for(slug)
    if config:
        merged.update(config)
    return merged


def _update_health_from_config(integration: Integration) -> None:
    config = _merge_config(integration.slug, integration.config)
    if integration.slug in LAB_ONLY_IMPORT_SOURCES:
        integration.health_status = IntegrationHealth.HEALTHY
        if not integration.last_error:
            integration.last_error = "Import-only lab connector. Remote execution is disabled."
        return

    if not integration.enabled:
        integration.health_status = IntegrationHealth.OFFLINE
        if not integration.last_error:
            integration.last_error = "Integration disabled."
        return

    if not config.get("endpoint_url"):
        integration.health_status = IntegrationHealth.OFFLINE
        integration.last_error = "Configuration required before manual sync."


def update_integration_configuration(
    db: Session,
    *,
    slug: str,
    payload: IntegrationConfigUpdate,
    actor: User,
    ip_address: str | None,
) -> Integration:
    integration = _integration_or_404(db, slug)
    sync_configuration_fields = {
        "endpoint_url",
        "auth_type",
        "username",
        "password",
        "api_token",
        "verify_tls",
        "timeout_seconds",
        "lookback_minutes",
        "request_headers",
        "query_params",
    }
    provided_fields = set(payload.model_dump(exclude_none=True).keys())
    if integration.slug in LAB_ONLY_IMPORT_SOURCES and provided_fields.intersection(sync_configuration_fields):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nmap and Hydra are import-only lab connectors and cannot be configured for remote sync",
        )

    next_config = _merge_config(integration.slug, integration.config)
    for key, value in payload.model_dump(exclude_none=True).items():
        if key == "enabled":
            integration.enabled = bool(value)
            continue
        next_config[key] = value
    integration.config = next_config
    if payload.enabled is not None:
        integration.enabled = payload.enabled

    if integration.slug in LAB_ONLY_IMPORT_SOURCES:
        integration.last_error = "Import-only lab connector. Remote execution is disabled."
        integration.health_status = IntegrationHealth.HEALTHY
    else:
        integration.last_error = None
        integration.health_status = IntegrationHealth.DEGRADED if next_config.get("endpoint_url") else IntegrationHealth.OFFLINE
        _update_health_from_config(integration)

    db.commit()
    db.refresh(integration)
    record_audit(
        db,
        actor=actor,
        action="integration.config_updated",
        entity_type="integration",
        entity_id=integration.id,
        details={"slug": integration.slug, "enabled": integration.enabled},
        ip_address=ip_address,
    )
    return integration


def _start_run(db: Session, integration: Integration, *, mode: str, source_filename: str | None) -> IntegrationRun:
    run = IntegrationRun(
        integration_id=integration.id,
        status="running",
        source_filename=source_filename,
        summary={"mode": mode},
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def _complete_run(
    db: Session,
    *,
    integration: Integration,
    run: IntegrationRun,
    summary: IngestionSummary,
) -> None:
    now = datetime.now(timezone.utc)
    integration.last_synced_at = now
    integration.last_error = None
    integration.health_status = IntegrationHealth.HEALTHY
    run.status = "completed"
    run.completed_at = now
    run.records_ingested = summary.normalized_records
    run.summary = {
        "mode": summary.mode,
        "status": summary.status,
        "input_format": summary.input_format,
        "alerts_created": summary.alerts_created,
        "alerts_updated": summary.alerts_updated,
        "logs_created": summary.logs_created,
        "assets_touched": summary.assets_touched,
        "incident_candidates": summary.incident_candidates,
        "normalized_records": summary.normalized_records,
        "imported_lab_data": summary.imported_lab_data,
    }
    db.commit()


def _fail_run(
    db: Session,
    *,
    integration: Integration,
    run: IntegrationRun,
    error: Exception,
    summary: IngestionSummary,
) -> None:
    now = datetime.now(timezone.utc)
    integration.health_status = IntegrationHealth.DEGRADED if _is_sync_capable(integration.slug) else IntegrationHealth.OFFLINE
    integration.last_error = str(error)
    run.status = "failed"
    run.completed_at = now
    run.error_message = str(error)
    run.records_ingested = summary.normalized_records
    run.summary = {
        "mode": summary.mode,
        "status": "failed",
        "input_format": summary.input_format,
        "alerts_created": summary.alerts_created,
        "alerts_updated": summary.alerts_updated,
        "logs_created": summary.logs_created,
        "assets_touched": summary.assets_touched,
        "incident_candidates": summary.incident_candidates,
        "normalized_records": summary.normalized_records,
        "imported_lab_data": summary.imported_lab_data,
    }
    db.commit()


def _build_http_request(integration: Integration) -> tuple[str, dict[str, str], httpx.BasicAuth | None, dict[str, Any], bool, float]:
    config = _merge_config(integration.slug, integration.config)
    endpoint_url = config.get("endpoint_url")
    if not endpoint_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Integration endpoint URL is not configured")

    headers = {str(key): str(value) for key, value in config.get("request_headers", {}).items()}
    query_params = {str(key): str(value) for key, value in config.get("query_params", {}).items()}
    lookback_minutes = int(config.get("lookback_minutes", 60))
    if lookback_minutes > 0:
        since = datetime.now(timezone.utc) - timedelta(minutes=lookback_minutes)
        query_params.setdefault("since", since.isoformat())

    auth: httpx.BasicAuth | None = None
    auth_type = str(config.get("auth_type", "none")).lower()
    if auth_type == "bearer" and config.get("api_token"):
        headers["Authorization"] = f"Bearer {config['api_token']}"
    elif auth_type == "basic" and config.get("username") and config.get("password"):
        auth = httpx.BasicAuth(config["username"], config["password"])

    return (
        endpoint_url,
        headers,
        auth,
        query_params,
        bool(config.get("verify_tls", True)),
        float(config.get("timeout_seconds", 15)),
    )


def fetch_remote_payload(integration: Integration) -> tuple[bytes, str | None]:
    endpoint_url, headers, auth, query_params, verify_tls, timeout_seconds = _build_http_request(integration)
    with httpx.Client(timeout=timeout_seconds, verify=verify_tls) as client:
        response = client.get(endpoint_url, headers=headers, auth=auth, params=query_params)
        response.raise_for_status()
        return response.content, response.headers.get("content-type")


def _ingest_payload(
    db: Session,
    *,
    integration: Integration,
    raw_bytes: bytes,
    filename: str,
    mode: str,
    actor: User,
    ip_address: str | None,
    run: IntegrationRun | None = None,
) -> IngestionSummary:
    run = run or _start_run(db, integration, mode=mode, source_filename=filename)
    summary = IngestionSummary(
        integration=integration.slug,
        run_id=run.id,
        mode=mode,
        status="running",
        imported_lab_data=integration.slug in LAB_ONLY_IMPORT_SOURCES,
    )

    try:
        parsed = parse_telemetry(integration.slug, raw_bytes, filename=filename)
        summary.input_format = parsed.input_format
        summary.normalized_records = len(parsed.records)
        assets_touched: set[str] = set()

        for record in parsed.records:
            asset = ensure_asset(
                db,
                hostname=record.asset_hostname or "unknown-asset",
                ip_address=record.asset_ip,
                operating_system=record.operating_system,
            )
            assets_touched.add(asset.id)

            existing_log = None
            if record.fingerprint:
                existing_log = (
                    db.query(LogEntry)
                    .filter(LogEntry.integration_id == integration.id, LogEntry.fingerprint == record.fingerprint)
                    .one_or_none()
                )
            if existing_log is None:
                db.add(
                    LogEntry(
                        source=integration.slug,
                        level=record.level,
                        category=record.category,
                        message=record.message,
                        event_timestamp=record.occurred_at or record.detected_at or datetime.now(timezone.utc),
                        asset_id=asset.id,
                        integration_id=integration.id,
                        raw_payload=record.raw_payload,
                        parsed_payload=record.parsed_payload,
                        fingerprint=record.fingerprint,
                    )
                )
                db.commit()
                summary.logs_created += 1

            if not record.should_create_alert:
                continue

            if record.incident_candidate:
                summary.incident_candidates += 1

            existing_alert = (
                db.query(Alert)
                .filter(Alert.source == integration.slug, Alert.external_id == record.external_id)
                .one_or_none()
            )
            if existing_alert is not None:
                summary.alerts_updated += 1
                continue

            alert = create_alert(
                db,
                title=record.title,
                description=record.description,
                source=integration.slug,
                source_type=record.source_type,
                event_type=record.event_type,
                severity=record.severity.value,
                occurred_at=record.occurred_at,
                tags=record.tags,
                raw_payload=record.raw_payload,
                parsed_payload={**record.parsed_payload, "fingerprint": record.fingerprint},
                asset_hostname=record.asset_hostname,
                asset_ip=record.asset_ip,
                actor=actor,
                ip_address=ip_address,
                integration=integration,
            )
            alert.external_id = record.external_id
            if record.detected_at:
                alert.detected_at = record.detected_at
            db.commit()
            db.refresh(alert)
            summary.alerts_created += 1
            summary.created_alerts.append(alert)

        summary.assets_touched = len(assets_touched)
        summary.status = "completed"
        _complete_run(db, integration=integration, run=run, summary=summary)
        record_audit(
            db,
            actor=actor,
            action="integration.ingested",
            entity_type="integration",
            entity_id=integration.id,
            details={"slug": integration.slug, "run_id": run.id, "mode": mode, "filename": filename},
            ip_address=ip_address,
        )
        return summary
    except Exception as error:
        _fail_run(db, integration=integration, run=run, error=error, summary=summary)
        if isinstance(error, HTTPException):
            raise
        if isinstance(error, ValueError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ingestion failed. Check integration run history for details.",
        ) from error


async def import_integration_file(
    db: Session,
    *,
    slug: str,
    filename: str,
    raw_bytes: bytes,
    actor: User,
    ip_address: str | None,
) -> IngestionSummary:
    integration = _integration_or_404(db, slug)
    summary = _ingest_payload(
        db,
        integration=integration,
        raw_bytes=raw_bytes,
        filename=filename,
        mode="import",
        actor=actor,
        ip_address=ip_address,
    )
    for alert in summary.created_alerts:
        await broadcast_alert_event(alert, "created")
    return summary


async def sync_integration(
    db: Session,
    *,
    slug: str,
    actor: User,
    ip_address: str | None,
) -> IngestionSummary:
    integration = _integration_or_404(db, slug)
    if integration.slug in LAB_ONLY_IMPORT_SOURCES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nmap and Hydra are import-only lab connectors and cannot be remotely synchronized",
        )

    run = _start_run(db, integration, mode="sync", source_filename=f"{integration.slug}-sync.json")
    try:
        payload, _content_type = fetch_remote_payload(integration)
    except Exception as error:
        summary = IngestionSummary(
            integration=integration.slug,
            run_id=run.id,
            mode="sync",
            status="failed",
            imported_lab_data=False,
        )
        _fail_run(db, integration=integration, run=run, error=error, summary=summary)
        if isinstance(error, HTTPException):
            raise
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error

    filename = f"{integration.slug}-sync.json"
    summary = _ingest_payload(
        db,
        integration=integration,
        raw_bytes=payload,
        filename=filename,
        mode="sync",
        actor=actor,
        ip_address=ip_address,
        run=run,
    )
    for alert in summary.created_alerts:
        await broadcast_alert_event(alert, "created")
    return summary
