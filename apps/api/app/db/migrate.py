from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from app.db.base import Base
from app.db.init_db import ensure_default_integrations
from app.db.session import SessionLocal, engine
from app.models.entities import (
    Alert,
    AlertSeverity,
    AlertStatus,
    Asset,
    AuditLog,
    Incident,
    IncidentAlertLink,
    IncidentEvent,
    IncidentPriority,
    IncidentStatus,
    Integration,
    IntegrationHealth,
    IntegrationType,
    LogEntry,
    ResponseRecommendation,
    User,
    UserRole,
)
from app.services.domain import _refresh_asset_risk

logger = logging.getLogger(__name__)

CURRENT_TABLES = set(Base.metadata.tables.keys())
LEGACY_TABLES = (
    "users",
    "alerts",
    "incidents",
    "log_entries",
    "virtual_machines",
    "integration_statuses",
    "reports",
)
LEGACY_SENTINELS = {"virtual_machines", "integration_statuses", "reports"}
LEGACY_PREFIX = "legacy_"
INCIDENT_SEQUENCE_NAME = "incident_reference_seq"

USER_ROLE_MAP = {
    "ADMIN": UserRole.ADMIN,
    "ANALYST": UserRole.ANALYST,
    "VIEWER": UserRole.VIEWER,
}
ALERT_SEVERITY_MAP = {
    "CRITICAL": AlertSeverity.CRITICAL,
    "HIGH": AlertSeverity.HIGH,
    "MEDIUM": AlertSeverity.MEDIUM,
    "LOW": AlertSeverity.LOW,
}
ALERT_STATUS_MAP = {
    "NEW": AlertStatus.OPEN,
    "TRIAGED": AlertStatus.TRIAGED,
    "INVESTIGATING": AlertStatus.INVESTIGATING,
    "RESOLVED": AlertStatus.RESOLVED,
}
INCIDENT_STATUS_MAP = {
    "OPEN": IncidentStatus.OPEN,
    "TRIAGED": IncidentStatus.MONITORING,
    "IN_PROGRESS": IncidentStatus.CONTAINED,
    "RESOLVED": IncidentStatus.RESOLVED,
}
INCIDENT_PRIORITY_MAP = {
    "CRITICAL": IncidentPriority.P1,
    "HIGH": IncidentPriority.P2,
    "MEDIUM": IncidentPriority.P3,
    "LOW": IncidentPriority.P4,
}
INTEGRATION_HEALTH_MAP = {
    "CONNECTED": IntegrationHealth.HEALTHY,
    "DEGRADED": IntegrationHealth.DEGRADED,
}


def _api_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _alembic_config() -> Config:
    api_root = _api_root()
    config = Config(str(api_root / "alembic.ini"))
    config.set_main_option("script_location", str(api_root / "alembic"))
    config.set_main_option("sqlalchemy.url", str(engine.url))
    return config


def _existing_tables() -> set[str]:
    with engine.connect() as connection:
        return set(inspect(connection).get_table_names())


def _legacy_table_name(name: str) -> str:
    return f"{LEGACY_PREFIX}{name}"


def _has_legacy_tables(tables: set[str]) -> bool:
    prefixed = {_legacy_table_name(name) for name in LEGACY_SENTINELS}
    return bool((LEGACY_SENTINELS & tables) or (prefixed & tables))


def _rename_legacy_tables() -> bool:
    renamed_any = False
    with engine.begin() as connection:
        tables = set(inspect(connection).get_table_names())
        for name in LEGACY_TABLES:
            legacy_name = _legacy_table_name(name)
            if name not in tables or legacy_name in tables:
                continue
            connection.execute(text(f'ALTER TABLE "{name}" RENAME TO "{legacy_name}"'))
            logger.info("Renamed legacy table %s -> %s", name, legacy_name)
            renamed_any = True
    return renamed_any


def _rename_legacy_indexes_and_constraints() -> None:
    with engine.begin() as connection:
        legacy_tables = [
            table_name
            for table_name in inspect(connection).get_table_names()
            if table_name.startswith(LEGACY_PREFIX)
        ]
        if not legacy_tables:
            return

        constraints = connection.execute(
            text(
                """
                SELECT conrelid::regclass::text AS table_name, conname
                FROM pg_constraint
                WHERE connamespace = 'public'::regnamespace
                  AND conrelid::regclass::text = ANY(:legacy_tables)
                ORDER BY conrelid::regclass::text, conname
                """
            ),
            {"legacy_tables": legacy_tables},
        ).mappings()
        existing_constraint_names = {
            str(row["conname"])
            for row in connection.execute(
                text(
                    """
                    SELECT conname
                    FROM pg_constraint
                    WHERE connamespace = 'public'::regnamespace
                    """
                )
            ).mappings()
        }
        for row in constraints:
            constraint_name = str(row["conname"])
            if constraint_name.startswith(LEGACY_PREFIX):
                continue
            next_name = f"{LEGACY_PREFIX}{constraint_name}"
            if next_name in existing_constraint_names:
                continue
            connection.execute(
                text(
                    f'ALTER TABLE "{row["table_name"]}" RENAME CONSTRAINT "{constraint_name}" TO "{next_name}"'
                )
            )
            existing_constraint_names.add(next_name)
            logger.info("Renamed legacy constraint %s -> %s", constraint_name, next_name)

        indexes = connection.execute(
            text(
                """
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
                  AND tablename = ANY(:legacy_tables)
                ORDER BY indexname
                """
            ),
            {"legacy_tables": legacy_tables},
        ).mappings()
        existing_index_names = {
            str(row["indexname"])
            for row in connection.execute(
                text(
                    """
                    SELECT indexname
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                    """
                )
            ).mappings()
        }
        for row in indexes:
            index_name = str(row["indexname"])
            if index_name.startswith(LEGACY_PREFIX):
                continue
            next_name = f"{LEGACY_PREFIX}{index_name}"
            if next_name in existing_index_names:
                continue
            connection.execute(text(f'ALTER INDEX "{index_name}" RENAME TO "{next_name}"'))
            existing_index_names.add(next_name)
            logger.info("Renamed legacy index %s -> %s", index_name, next_name)


def _drop_unversioned_current_tables() -> None:
    ordered_current_tables = [table.name for table in reversed(Base.metadata.sorted_tables)]
    with engine.begin() as connection:
        for table_name in ordered_current_tables:
            connection.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))
        connection.execute(text(f"DROP SEQUENCE IF EXISTS {INCIDENT_SEQUENCE_NAME} CASCADE"))
    logger.info("Dropped unversioned current-schema tables before rebuilding under Alembic control.")


def _ensure_incident_sequence() -> None:
    with engine.begin() as connection:
        connection.execute(text(f"CREATE SEQUENCE IF NOT EXISTS {INCIDENT_SEQUENCE_NAME} START 1 INCREMENT 1"))


def _upgrade_schema() -> None:
    command.upgrade(_alembic_config(), "head")


def _stamp_schema() -> None:
    command.stamp(_alembic_config(), "head")


def _stable_id(kind: str, key: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"https://aegiscore.local/{kind}/{key.strip().lower()}"))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _risk_score_from_legacy(
    *,
    confidence_score: float | None,
    anomaly_score: float | None,
    severity: AlertSeverity,
    is_anomalous: bool,
) -> float:
    confidence_component = max(0.0, min(float(confidence_score or 0.0), 1.0)) * 60
    anomaly_component = max(0.0, min(float(anomaly_score or 0.0), 1.0)) * 25
    severity_bonus = {
        AlertSeverity.CRITICAL: 15,
        AlertSeverity.HIGH: 10,
        AlertSeverity.MEDIUM: 5,
        AlertSeverity.LOW: 0,
    }[severity]
    anomaly_bonus = 10 if is_anomalous else 0
    return round(min(100.0, confidence_component + anomaly_component + severity_bonus + anomaly_bonus), 2)


def _risk_band(score: float) -> str:
    if score >= 85:
        return "critical"
    if score >= 70:
        return "high"
    if score >= 50:
        return "medium"
    return "low"


def _source_type_for_tool(tool: str) -> str:
    if tool in {IntegrationType.NMAP.value, IntegrationType.HYDRA.value}:
        return "lab-import"
    if tool == "virtualbox":
        return "infrastructure"
    return "telemetry"


def _legacy_recommendations(tool: str, severity: AlertSeverity) -> list[dict[str, str | int | None]]:
    items = [
        {
            "title": "Validate imported context",
            "description": "Review the migrated event details and confirm the affected host, tool, and surrounding telemetry.",
            "priority": 1,
        },
        {
            "title": "Assign analyst follow-up",
            "description": "Capture ownership and the next verification step inside the alert workflow.",
            "priority": 2,
        },
    ]
    if tool in {IntegrationType.WAZUH.value, IntegrationType.SURICATA.value, "virtualbox"}:
        items.append(
            {
                "title": "Correlate with related platform telemetry",
                "description": "Review nearby endpoint, network, or infrastructure events before changing alert status.",
                "priority": 3,
            }
        )
    if severity in {AlertSeverity.CRITICAL, AlertSeverity.HIGH}:
        items.append(
            {
                "title": "Escalate to incident if confirmed",
                "description": "Promote the finding into an incident when the risk remains active after review.",
                "priority": 4,
            }
        )
    return items


def _build_alert_explainability(row: dict, *, tool: str) -> list[dict[str, str | float | None]]:
    explainability = [
        {
            "factor": "legacy_confidence_score",
            "label": "Legacy confidence score",
            "detail": "Imported from the pre-Alembic AegisCore dataset.",
            "impact": round(float(row.get("confidence_score") or 0.0) * 100, 2),
            "value": round(float(row.get("confidence_score") or 0.0), 4),
            "category": "historical",
        },
        {
            "factor": "legacy_anomaly_score",
            "label": "Legacy anomaly score",
            "detail": str(row.get("anomaly_explanation") or "Imported anomaly context."),
            "impact": round(float(row.get("anomaly_score") or 0.0) * 100, 2),
            "value": round(float(row.get("anomaly_score") or 0.0), 4),
            "category": "historical",
        },
    ]
    if row.get("is_anomalous"):
        explainability.append(
            {
                "factor": "legacy_anomalous_flag",
                "label": "Legacy anomaly flag",
                "detail": f"Flagged as anomalous by the previous {tool} workflow.",
                "impact": 15.0,
                "value": 1.0,
                "category": "historical",
            }
        )
    return explainability


def _legacy_table_exists(table_name: str) -> bool:
    return table_name in _existing_tables()


def _load_legacy_rows(table_name: str) -> list[dict]:
    if not _legacy_table_exists(table_name):
        return []
    with SessionLocal() as db:
        return [dict(row) for row in db.execute(text(f'SELECT * FROM "{table_name}"')).mappings().all()]


def _ensure_asset(
    db,
    *,
    hostname: str,
    ip_address: str | None = None,
    operating_system: str | None = None,
    business_unit: str | None = None,
    risk_summary: str | None = None,
    observed_at: datetime | None = None,
    criticality: int = 3,
) -> Asset:
    normalized_hostname = hostname.strip()
    asset = db.query(Asset).filter(Asset.hostname == normalized_hostname).one_or_none()
    created_at = observed_at or _utcnow()
    if asset is None:
        asset = Asset(
            id=_stable_id("legacy-asset", normalized_hostname),
            hostname=normalized_hostname,
            ip_address=ip_address,
            operating_system=operating_system,
            business_unit=business_unit,
            criticality=criticality,
            risk_summary=risk_summary,
            last_seen_at=observed_at,
            created_at=created_at,
            updated_at=created_at,
        )
        db.add(asset)
        db.flush()
        return asset

    if ip_address and not asset.ip_address:
        asset.ip_address = ip_address
    if operating_system and not asset.operating_system:
        asset.operating_system = operating_system
    if business_unit and not asset.business_unit:
        asset.business_unit = business_unit
    if risk_summary and not asset.risk_summary:
        asset.risk_summary = risk_summary
    if observed_at and (asset.last_seen_at is None or observed_at > asset.last_seen_at):
        asset.last_seen_at = observed_at
    if observed_at and observed_at > asset.updated_at:
        asset.updated_at = observed_at
    return asset


def _migrate_legacy_data() -> None:
    legacy_users = _load_legacy_rows("legacy_users")
    legacy_alerts = _load_legacy_rows("legacy_alerts")
    legacy_incidents = _load_legacy_rows("legacy_incidents")
    legacy_logs = _load_legacy_rows("legacy_log_entries")
    legacy_vms = _load_legacy_rows("legacy_virtual_machines")
    legacy_integrations = _load_legacy_rows("legacy_integration_statuses")
    legacy_reports = _load_legacy_rows("legacy_reports")
    if not any((legacy_users, legacy_alerts, legacy_incidents, legacy_logs, legacy_vms, legacy_integrations, legacy_reports)):
        return

    with SessionLocal() as db:
        ensure_default_integrations(db)
        integrations_by_slug = {integration.slug: integration for integration in db.query(Integration).all()}

        for row in legacy_users:
            email = str(row["email"]).strip().lower()
            user = db.get(User, row["id"]) or db.query(User).filter(User.email == email).one_or_none()
            if user is None:
                user = User(
                    id=row["id"],
                    email=email,
                    full_name=str(row["full_name"]).strip(),
                    role=USER_ROLE_MAP.get(str(row["role"]).upper(), UserRole.ANALYST),
                    password_hash=str(row["password_hash"]),
                    is_active=bool(row["is_active"]),
                    last_login_at=None,
                    created_at=row["created_at"],
                    updated_at=row["created_at"],
                )
                db.add(user)
            else:
                user.email = email
                user.full_name = str(row["full_name"]).strip()
                user.role = USER_ROLE_MAP.get(str(row["role"]).upper(), UserRole.ANALYST)
                user.password_hash = str(row["password_hash"])
                user.is_active = bool(row["is_active"])
                user.created_at = row["created_at"]
                user.updated_at = row["created_at"]

        db.flush()

        for row in legacy_vms:
            _ensure_asset(
                db,
                hostname=str(row["vm_name"]),
                ip_address=row.get("ip_address"),
                operating_system=row.get("os_type"),
                business_unit=row.get("role"),
                risk_summary=row.get("notes"),
                observed_at=None,
            )

        for row in (*legacy_alerts, *legacy_logs):
            source_host = str(row.get("source") or "").strip()
            if not source_host:
                continue
            observed_at = row.get("created_at")
            _ensure_asset(
                db,
                hostname=source_host,
                observed_at=observed_at,
                risk_summary="Imported from legacy AegisCore monitoring data.",
            )

        for row in legacy_integrations:
            slug = str(row["tool_name"]).strip().lower()
            integration = integrations_by_slug.get(slug)
            if integration is None:
                continue
            integration.enabled = True
            integration.last_synced_at = row.get("last_sync_at")
            integration.last_error = str(row.get("notes") or "").strip() or None
            if slug in {IntegrationType.NMAP.value, IntegrationType.HYDRA.value}:
                integration.health_status = IntegrationHealth.HEALTHY
            else:
                integration.health_status = INTEGRATION_HEALTH_MAP.get(
                    str(row.get("status") or "").upper(),
                    IntegrationHealth.OFFLINE,
                )

        db.flush()

        for row in legacy_alerts:
            tool = str(row["source_tool"]).strip().lower()
            severity = ALERT_SEVERITY_MAP.get(str(row["severity"]).upper(), AlertSeverity.MEDIUM)
            status = ALERT_STATUS_MAP.get(str(row["status"]).upper(), AlertStatus.OPEN)
            source_host = str(row["source"]).strip()
            asset = db.query(Asset).filter(Asset.hostname == source_host).one_or_none() if source_host else None
            integration = integrations_by_slug.get(tool)
            risk_score = _risk_score_from_legacy(
                confidence_score=row.get("confidence_score"),
                anomaly_score=row.get("anomaly_score"),
                severity=severity,
                is_anomalous=bool(row.get("is_anomalous")),
            )
            alert = db.get(Alert, row["id"])
            if alert is None:
                alert = Alert(id=row["id"])
                db.add(alert)
            alert.title = str(row["title"]).strip()
            alert.description = str(row.get("description") or "").strip() or None
            alert.source = tool
            alert.source_type = _source_type_for_tool(tool)
            alert.event_type = None
            alert.severity = severity
            alert.status = status
            alert.risk_score = risk_score
            alert.risk_label = _risk_band(risk_score)
            alert.explainability = _build_alert_explainability(row, tool=tool)
            alert.explanation_summary = str(row.get("anomaly_explanation") or "").strip() or None
            alert.recommendations = [item["title"] for item in _legacy_recommendations(tool, severity)]
            alert.occurred_at = row["created_at"]
            alert.detected_at = row["created_at"]
            alert.asset_id = asset.id if asset else None
            alert.integration_id = integration.id if integration else None
            alert.tags = sorted(
                {
                    "legacy-migrated",
                    tool,
                    "anomalous" if row.get("is_anomalous") else "baseline",
                }
            )
            alert.raw_payload = {
                "legacy_source_host": source_host,
                "legacy_source_tool": tool,
                "legacy_confidence_score": float(row.get("confidence_score") or 0.0),
                "legacy_anomaly_score": float(row.get("anomaly_score") or 0.0),
                "legacy_anomalous": bool(row.get("is_anomalous")),
            }
            alert.parsed_payload = {
                "legacy_imported": True,
                "legacy_source_host": source_host,
                "legacy_anomaly_explanation": row.get("anomaly_explanation"),
            }
            alert.created_at = row["created_at"]
            alert.updated_at = row["created_at"]

            if asset is not None and (asset.last_seen_at is None or row["created_at"] > asset.last_seen_at):
                asset.last_seen_at = row["created_at"]

            existing_recommendations = (
                db.query(ResponseRecommendation).filter(ResponseRecommendation.alert_id == alert.id).count()
            )
            if existing_recommendations == 0:
                for index, item in enumerate(_legacy_recommendations(tool, severity), start=1):
                    db.add(
                        ResponseRecommendation(
                            id=_stable_id("legacy-alert-recommendation", f"{alert.id}:{index}"),
                            alert_id=alert.id,
                            title=str(item["title"]),
                            description=str(item["description"]) if item.get("description") else None,
                            priority=int(item["priority"]),
                            created_at=row["created_at"],
                        )
                    )

        db.flush()

        for row in legacy_incidents:
            incident = db.get(Incident, row["id"])
            legacy_status = str(row.get("status") or "").upper()
            linked_alert = db.get(Alert, row.get("alert_id")) if row.get("alert_id") else None
            if incident is None:
                incident = Incident(id=row["id"])
                db.add(incident)
            incident.reference = f"LEGACY-{row['id']}"
            incident.title = (
                f"Legacy investigation: {linked_alert.title}"
                if linked_alert is not None
                else "Legacy incident import"
            )
            incident.description = str(row.get("notes") or "").strip() or None
            incident.status = INCIDENT_STATUS_MAP.get(legacy_status, IncidentStatus.OPEN)
            incident.priority = INCIDENT_PRIORITY_MAP.get(str(row.get("priority") or "").upper(), IncidentPriority.P3)
            incident.assignee_id = row.get("assigned_to_user_id")
            incident.created_by_id = None
            incident.opened_at = row["opened_at"]
            incident.resolved_at = row.get("closed_at")
            incident.resolution_notes = (
                str(row.get("notes") or "").strip() or None
                if legacy_status == "RESOLVED"
                else None
            )
            incident.evidence = [{"source": "legacy-incident-table", "note": "Imported from pre-Alembic schema."}]
            incident.created_at = row["opened_at"]
            incident.updated_at = row.get("closed_at") or row["opened_at"]

            if linked_alert is not None:
                link_id = _stable_id("legacy-incident-alert-link", f"{incident.id}:{linked_alert.id}")
                if db.get(IncidentAlertLink, link_id) is None:
                    db.add(
                        IncidentAlertLink(
                            id=link_id,
                            incident_id=incident.id,
                            alert_id=linked_alert.id,
                        )
                    )

            event_id = _stable_id("legacy-incident-event", f"{incident.id}:initial")
            if db.get(IncidentEvent, event_id) is None:
                db.add(
                    IncidentEvent(
                        id=event_id,
                        incident_id=incident.id,
                        author_id=row.get("assigned_to_user_id"),
                        event_type="note",
                        body=str(row.get("notes") or "Legacy incident imported.").strip(),
                        event_metadata={
                            "legacy_imported": True,
                            "legacy_status": legacy_status,
                        },
                        is_timeline_event=True,
                        created_at=row["opened_at"],
                    )
                )

        for row in legacy_logs:
            tool = str(row["source_tool"]).strip().lower()
            source_host = str(row["source"]).strip()
            asset = db.query(Asset).filter(Asset.hostname == source_host).one_or_none() if source_host else None
            integration = integrations_by_slug.get(tool)
            raw_payload = dict(row.get("raw_log") or {})
            parsed_payload = dict(row.get("normalized_log") or {})
            parsed_payload.setdefault("legacy_source_host", source_host)
            parsed_payload["legacy_imported"] = True
            message = (
                str(parsed_payload.get("message") or raw_payload.get("message") or row.get("event_type") or "Legacy log import")
                .strip()
            )
            log_entry = db.get(LogEntry, row["id"])
            if log_entry is None:
                log_entry = LogEntry(id=row["id"])
                db.add(log_entry)
            log_entry.source = tool
            log_entry.level = str(row.get("severity") or "info").lower()
            log_entry.category = str(row.get("event_type") or "").strip() or None
            log_entry.message = message
            log_entry.event_timestamp = row["created_at"]
            log_entry.asset_id = asset.id if asset else None
            log_entry.integration_id = integration.id if integration else None
            log_entry.raw_payload = raw_payload
            log_entry.parsed_payload = parsed_payload
            log_entry.fingerprint = None
            log_entry.created_at = row["created_at"]

            if asset is not None and (asset.last_seen_at is None or row["created_at"] > asset.last_seen_at):
                asset.last_seen_at = row["created_at"]

        for row in legacy_reports:
            audit_id = _stable_id("legacy-report-audit", str(row["id"]))
            if db.get(AuditLog, audit_id) is not None:
                continue
            db.add(
                AuditLog(
                    id=audit_id,
                    actor_user_id=row.get("generated_by_user_id"),
                    action="legacy.report_imported",
                    entity_type="report",
                    entity_id=row["id"],
                    details={
                        "legacy_imported": True,
                        "title": row.get("title"),
                        "report_type": str(row.get("report_type") or ""),
                        "status": str(row.get("status") or ""),
                        "content": row.get("content_json") or {},
                    },
                    ip_address=None,
                    created_at=row["created_at"],
                )
            )

        db.flush()

        for asset in db.query(Asset).all():
            _refresh_asset_risk(asset, db)

        migration_audit_id = _stable_id("legacy-schema-migration-audit", "legacy-v1-to-current")
        if db.get(AuditLog, migration_audit_id) is None:
            db.add(
                AuditLog(
                    id=migration_audit_id,
                    actor_user_id=None,
                    action="database.legacy_schema_migrated",
                    entity_type="database",
                    entity_id="legacy-schema",
                    details={
                        "users": len(legacy_users),
                        "alerts": len(legacy_alerts),
                        "incidents": len(legacy_incidents),
                        "logs": len(legacy_logs),
                        "virtual_machines": len(legacy_vms),
                        "integration_statuses": len(legacy_integrations),
                        "reports": len(legacy_reports),
                    },
                    ip_address=None,
                    created_at=_utcnow(),
                )
            )

        db.commit()
    logger.info("Imported legacy AegisCore data into the current schema.")


def ensure_database_schema() -> None:
    if engine.dialect.name != "postgresql":
        Base.metadata.create_all(bind=engine)
        return

    initial_tables = _existing_tables()
    legacy_present = _has_legacy_tables(initial_tables)
    alembic_present = "alembic_version" in initial_tables

    if legacy_present and LEGACY_SENTINELS & initial_tables:
        _rename_legacy_tables()
        initial_tables = _existing_tables()

    if _has_legacy_tables(initial_tables) and "alembic_version" not in initial_tables:
        _rename_legacy_indexes_and_constraints()
        current_tables_present = CURRENT_TABLES & initial_tables
        if current_tables_present:
            _drop_unversioned_current_tables()
            initial_tables = _existing_tables()

    if "alembic_version" in initial_tables:
        _upgrade_schema()
    elif CURRENT_TABLES.issubset(initial_tables):
        _ensure_incident_sequence()
        _stamp_schema()
    elif CURRENT_TABLES & initial_tables:
        current_tables_present = ", ".join(sorted(CURRENT_TABLES & initial_tables))
        raise RuntimeError(
            "Found a partially created current schema without Alembic version tracking. "
            f"Existing tables: {current_tables_present}. "
            "If this was created manually, start from a clean database or restore from backup."
        )
    else:
        _upgrade_schema()

    if _has_legacy_tables(_existing_tables()):
        _migrate_legacy_data()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ensure_database_schema()


if __name__ == "__main__":
    main()
