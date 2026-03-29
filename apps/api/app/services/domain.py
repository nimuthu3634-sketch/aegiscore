from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from io import StringIO

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.ingestion.parsers import parse_telemetry
from app.ml.scoring import score_alert
from app.models.entities import (
    Alert,
    AlertComment,
    AlertSeverity,
    AlertStatus,
    Asset,
    Incident,
    IncidentAlertLink,
    IncidentEvent,
    IncidentPriority,
    IncidentStatus,
    Integration,
    IntegrationHealth,
    IntegrationRun,
    LogEntry,
    ResponseRecommendation,
    User,
)
from app.schemas.domain import DashboardActivityItem, DashboardKpi, DashboardSummary, DashboardTrendPoint
from app.services.audit import record_audit
from app.services.realtime import manager


class ImportSummary:
    def __init__(
        self,
        *,
        integration: str,
        run_id: str,
        alerts_created: int,
        logs_created: int,
        assets_touched: int,
        incident_candidates: int,
    ) -> None:
        self.integration = integration
        self.run_id = run_id
        self.alerts_created = alerts_created
        self.logs_created = logs_created
        self.assets_touched = assets_touched
        self.incident_candidates = incident_candidates


def ensure_asset(
    db: Session,
    *,
    hostname: str,
    ip_address: str | None = None,
    operating_system: str | None = None,
    criticality: int = 3,
) -> Asset:
    asset = db.query(Asset).filter(Asset.hostname == hostname).one_or_none()
    if asset is None:
        asset = Asset(hostname=hostname, ip_address=ip_address, operating_system=operating_system, criticality=criticality)
        db.add(asset)
    else:
        asset.ip_address = ip_address or asset.ip_address
        asset.operating_system = operating_system or asset.operating_system
        asset.criticality = criticality or asset.criticality

    asset.last_seen_at = datetime.now(timezone.utc)
    db.flush()
    return asset


def _refresh_asset_risk(asset: Asset | None) -> None:
    if asset is None:
        return
    open_alerts = [alert for alert in asset.alerts if alert.status not in {AlertStatus.RESOLVED, AlertStatus.SUPPRESSED}]
    if not open_alerts:
        asset.risk_score = 0
        asset.risk_summary = "No active alert pressure."
        return

    average_score = sum(alert.risk_score for alert in open_alerts) / len(open_alerts)
    asset.risk_score = round(min(100, average_score + len(open_alerts) * 2), 2)
    asset.risk_summary = f"{len(open_alerts)} active alerts across endpoint and telemetry sources."


def _build_recommendations(source: str, severity: str, tags: list[str]) -> list[dict[str, str | int | None]]:
    source_lower = source.lower()
    tags_text = " ".join(tags).lower()
    items = [
        {
            "title": "Validate telemetry context",
            "description": "Confirm the source event, asset identity, and surrounding log context before triage.",
            "priority": 1,
        },
        {
            "title": "Assign analyst ownership",
            "description": "Capture owner, triage notes, and escalation decision inside the alert record.",
            "priority": 2,
        },
    ]
    if source_lower in {"wazuh", "suricata"}:
        items.append(
            {
                "title": "Review supporting defensive telemetry",
                "description": "Correlate the imported signal with other endpoint or network logs from the same period.",
                "priority": 3,
            }
        )
    if severity in {AlertSeverity.CRITICAL.value, AlertSeverity.HIGH.value} or "credential" in tags_text or "auth" in tags_text:
        items.append(
            {
                "title": "Escalate to incident if confirmed",
                "description": "Create an incident when the signal indicates repeated control failure or active compromise risk.",
                "priority": 4,
            }
        )
    return items


async def broadcast_alert_event(alert: Alert, event: str) -> None:
    await manager.broadcast(
        "alerts",
        {
            "event": event,
            "alert_id": alert.id,
            "title": alert.title,
            "severity": alert.severity,
            "status": alert.status,
            "risk_score": alert.risk_score,
            "occurred_at": alert.occurred_at.isoformat(),
            "detected_at": alert.detected_at.isoformat(),
        },
    )


def create_alert(
    db: Session,
    *,
    title: str,
    description: str | None,
    source: str,
    severity: str,
    tags: list[str],
    raw_payload: dict,
    parsed_payload: dict,
    asset_hostname: str | None,
    asset_ip: str | None,
    actor: User | None,
    ip_address: str | None,
    integration: Integration | None = None,
    source_type: str = "telemetry",
    event_type: str | None = None,
    occurred_at: datetime | None = None,
) -> Alert:
    asset = ensure_asset(db, hostname=asset_hostname or "unknown-asset", ip_address=asset_ip) if asset_hostname else None
    open_asset_alerts = (
        len([entry for entry in asset.alerts if entry.status not in {AlertStatus.RESOLVED, AlertStatus.SUPPRESSED}]) if asset else 0
    )
    risk_score, explainability, risk_label = score_alert(
        {
            "title": title,
            "description": description,
            "source": source,
            "severity": severity,
            "tags": tags,
            "asset_criticality": asset.criticality if asset else 3,
            "open_asset_alerts": open_asset_alerts,
        }
    )
    recommendation_items = _build_recommendations(source, severity, tags)
    explanation_summary = (
        f"Prioritized as {risk_label} risk based on severity, asset criticality, alert density, and signal context."
    )

    alert = Alert(
        title=title,
        description=description,
        source=source,
        source_type=source_type,
        event_type=event_type,
        severity=severity,
        tags=tags,
        raw_payload=raw_payload,
        parsed_payload=parsed_payload,
        asset=asset,
        integration=integration,
        risk_score=risk_score,
        explainability=explainability,
        explanation_summary=explanation_summary,
        risk_label=risk_label,
        recommendations=[str(item["title"]) for item in recommendation_items],
        occurred_at=occurred_at or datetime.now(timezone.utc),
    )
    db.add(alert)
    db.flush()

    for item in recommendation_items:
        db.add(
            ResponseRecommendation(
                alert_id=alert.id,
                title=str(item["title"]),
                description=str(item["description"]) if item["description"] else None,
                priority=int(item["priority"]),
            )
        )

    _refresh_asset_risk(asset)
    db.commit()
    db.refresh(alert)

    record_audit(
        db,
        actor=actor,
        action="alert.created",
        entity_type="alert",
        entity_id=alert.id,
        details={"source": source, "severity": severity, "source_type": source_type, "event_type": event_type},
        ip_address=ip_address,
    )
    return alert


def update_alert(db: Session, alert: Alert, *, payload: dict, actor: User, ip_address: str | None) -> Alert:
    for field, value in payload.items():
        if value is None and field != "assigned_to_id":
            continue
        setattr(alert, field, value)
    _refresh_asset_risk(alert.asset)
    db.add(alert)
    db.commit()
    db.refresh(alert)

    record_audit(
        db,
        actor=actor,
        action="alert.updated",
        entity_type="alert",
        entity_id=alert.id,
        details=payload,
        ip_address=ip_address,
    )
    return alert


def add_alert_comment(db: Session, *, alert: Alert, actor: User, body: str, ip_address: str | None) -> AlertComment:
    comment = AlertComment(alert_id=alert.id, author_id=actor.id, body=body)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    record_audit(
        db,
        actor=actor,
        action="alert.comment_added",
        entity_type="alert",
        entity_id=alert.id,
        details={"comment_id": comment.id},
        ip_address=ip_address,
    )
    return comment


def create_incident(
    db: Session,
    *,
    title: str,
    description: str | None,
    priority: IncidentPriority,
    assignee_id: str | None,
    linked_alert_ids: list[str],
    evidence: list[dict],
    actor: User,
    ip_address: str | None,
) -> Incident:
    total_incidents = db.query(func.count(Incident.id)).scalar() or 0
    incident = Incident(
        reference=f"INC-{datetime.now(timezone.utc):%Y%m%d}-{total_incidents + 1:04d}",
        title=title,
        description=description,
        priority=priority,
        assignee_id=assignee_id,
        created_by_id=actor.id,
        evidence=evidence,
    )
    db.add(incident)
    db.flush()

    for alert_id in linked_alert_ids:
        alert = db.query(Alert).filter(Alert.id == alert_id).one_or_none()
        if alert is None:
            continue
        db.add(IncidentAlertLink(incident_id=incident.id, alert_id=alert.id))
        alert.status = AlertStatus.INVESTIGATING

    event = IncidentEvent(
        incident_id=incident.id,
        author_id=actor.id,
        event_type="status-change",
        body="Incident created and triage initiated.",
        event_metadata={"status": IncidentStatus.OPEN.value},
        is_timeline_event=True,
    )
    db.add(event)
    db.commit()
    db.refresh(incident)

    record_audit(
        db,
        actor=actor,
        action="incident.created",
        entity_type="incident",
        entity_id=incident.id,
        details={"reference": incident.reference, "linked_alert_count": len(linked_alert_ids)},
        ip_address=ip_address,
    )
    return incident


def add_incident_note(
    db: Session,
    *,
    incident: Incident,
    actor: User,
    body: str,
    is_timeline_event: bool,
    ip_address: str | None,
    event_type: str = "note",
    event_metadata: dict | None = None,
) -> IncidentEvent:
    event = IncidentEvent(
        incident_id=incident.id,
        author_id=actor.id,
        body=body,
        event_type=event_type,
        event_metadata=event_metadata or {},
        is_timeline_event=is_timeline_event,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    record_audit(
        db,
        actor=actor,
        action="incident.event_added",
        entity_type="incident",
        entity_id=incident.id,
        details={"timeline": is_timeline_event, "event_type": event_type},
        ip_address=ip_address,
    )
    return event


def update_incident(db: Session, incident: Incident, payload: dict, actor: User, ip_address: str | None) -> Incident:
    previous_status = incident.status
    for field, value in payload.items():
        if value is None:
            continue
        setattr(incident, field, value)
    if incident.status == IncidentStatus.RESOLVED and incident.resolved_at is None:
        incident.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(incident)
    if previous_status != incident.status:
        db.add(
            IncidentEvent(
                incident_id=incident.id,
                author_id=actor.id,
                event_type="status-change",
                body=f"Incident status changed from {previous_status} to {incident.status}.",
                event_metadata={"from": previous_status, "to": incident.status},
                is_timeline_event=True,
            )
        )
        db.commit()

    record_audit(
        db,
        actor=actor,
        action="incident.updated",
        entity_type="incident",
        entity_id=incident.id,
        details=payload,
        ip_address=ip_address,
    )
    return incident


def import_telemetry(
    db: Session,
    *,
    source: str,
    filename: str,
    raw_bytes: bytes,
    actor: User,
    ip_address: str | None,
) -> ImportSummary:
    integration = db.query(Integration).filter(Integration.slug == source).one_or_none()
    if integration is None:
        raise ValueError("Unknown integration")

    parsed_records = parse_telemetry(source, raw_bytes)
    run = IntegrationRun(integration_id=integration.id, status="running", source_filename=filename)
    db.add(run)
    db.flush()

    alerts_created = 0
    logs_created = 0
    assets: set[str] = set()
    incident_candidates = 0

    for record in parsed_records:
        asset = ensure_asset(db, hostname=record["asset_hostname"], ip_address=record.get("asset_ip"))
        assets.add(asset.id)
        log = LogEntry(
            source=source,
            level=record["level"],
            category=record["category"],
            message=record["message"],
            asset_id=asset.id,
            integration_id=integration.id,
            raw_payload=record["raw_payload"],
            parsed_payload=record["parsed_payload"],
        )
        db.add(log)
        logs_created += 1

        create_alert(
            db,
            title=record["title"],
            description=record["description"],
            source=source,
            source_type=record.get("source_type", "telemetry"),
            event_type=record.get("event_type"),
            severity=record["severity"],
            tags=record["tags"],
            raw_payload=record["raw_payload"],
            parsed_payload=record["parsed_payload"],
            asset_hostname=record["asset_hostname"],
            asset_ip=record.get("asset_ip"),
            actor=actor,
            ip_address=ip_address,
            integration=integration,
            occurred_at=record.get("occurred_at"),
        )
        alerts_created += 1
        incident_candidates += 1 if record["incident_candidate"] else 0

    integration.last_synced_at = datetime.now(timezone.utc)
    integration.health_status = IntegrationHealth.HEALTHY
    run.status = "completed"
    run.completed_at = datetime.now(timezone.utc)
    run.records_ingested = len(parsed_records)
    run.summary = {
        "alerts_created": alerts_created,
        "logs_created": logs_created,
        "assets_touched": len(assets),
        "incident_candidates": incident_candidates,
    }
    db.commit()
    db.refresh(run)

    record_audit(
        db,
        actor=actor,
        action="integration.imported",
        entity_type="integration",
        entity_id=integration.id,
        details={"source": source, "run_id": run.id, "filename": filename},
        ip_address=ip_address,
    )
    return ImportSummary(
        integration=source,
        run_id=run.id,
        alerts_created=alerts_created,
        logs_created=logs_created,
        assets_touched=len(assets),
        incident_candidates=incident_candidates,
    )


def build_dashboard_summary(db: Session) -> DashboardSummary:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    open_alerts = db.query(Alert).filter(Alert.status.notin_([AlertStatus.RESOLVED, AlertStatus.SUPPRESSED])).all()
    assets = db.query(Asset).order_by(desc(Asset.risk_score)).limit(5).all()
    incidents = db.query(Incident).filter(Incident.status != IncidentStatus.RESOLVED).all()
    logs_today = db.query(func.count(LogEntry.id)).filter(LogEntry.created_at >= today_start).scalar() or 0

    severity_breakdown = defaultdict(int)
    for alert in open_alerts:
        severity_breakdown[alert.severity] += 1

    trend_by_day: dict[str, dict[str, int]] = {}
    for offset in range(6, -1, -1):
        day = (today_start - timedelta(days=offset)).date()
        trend_by_day[day.isoformat()] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    recent_alerts = db.query(Alert).filter(Alert.detected_at >= today_start - timedelta(days=6)).all()
    for alert in recent_alerts:
        day_key = alert.detected_at.date().isoformat()
        if day_key in trend_by_day:
            trend_by_day[day_key][alert.severity] += 1

    integrations = db.query(Integration).all()
    health = {integration.name: integration.health_status for integration in integrations}

    activity: list[DashboardActivityItem] = []
    recent_alert_events = db.query(Alert).order_by(desc(Alert.created_at)).limit(4).all()
    recent_incidents = db.query(Incident).order_by(desc(Incident.created_at)).limit(4).all()
    for alert in recent_alert_events:
        activity.append(
            DashboardActivityItem(
                id=alert.id,
                timestamp=alert.created_at,
                title=alert.title,
                kind="alert",
                summary=f"{alert.severity.title()} alert from {alert.source}",
            )
        )
    for incident in recent_incidents:
        activity.append(
            DashboardActivityItem(
                id=incident.id,
                timestamp=incident.created_at,
                title=incident.reference,
                kind="incident",
                summary=incident.title,
            )
        )
    activity.sort(key=lambda item: item.timestamp, reverse=True)

    average_risk = round(sum(alert.risk_score for alert in open_alerts) / len(open_alerts), 2) if open_alerts else 0
    kpis = DashboardKpi(
        total_assets=db.query(func.count(Asset.id)).scalar() or 0,
        open_alerts=len(open_alerts),
        open_incidents=len(incidents),
        ingestion_today=int(logs_today),
        average_risk_score=average_risk,
    )

    trend = [DashboardTrendPoint(label=label, **values) for label, values in trend_by_day.items()]

    return DashboardSummary(
        kpis=kpis,
        severity_breakdown=dict(severity_breakdown),
        integration_health=health,
        alert_trend=trend,
        risky_assets=assets,
        recent_activity=activity[:8],
    )


def render_alerts_csv(alerts: list[Alert]) -> str:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["id", "title", "source", "source_type", "event_type", "severity", "status", "risk_score", "asset", "detected_at"]
    )
    for alert in alerts:
        writer.writerow(
            [
                alert.id,
                alert.title,
                alert.source,
                alert.source_type,
                alert.event_type or "",
                alert.severity,
                alert.status,
                alert.risk_score,
                alert.asset.hostname if alert.asset else "",
                alert.detected_at.isoformat(),
            ]
        )
    return output.getvalue()


def render_dashboard_csv(summary: DashboardSummary) -> str:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["metric", "value"])
    writer.writerow(["total_assets", summary.kpis.total_assets])
    writer.writerow(["open_alerts", summary.kpis.open_alerts])
    writer.writerow(["open_incidents", summary.kpis.open_incidents])
    writer.writerow(["ingestion_today", summary.kpis.ingestion_today])
    writer.writerow(["average_risk_score", summary.kpis.average_risk_score])
    return output.getvalue()


def incident_summary_text(incident: Incident) -> str:
    linked_alerts = ", ".join(link.alert.title for link in incident.alert_links) or "None"
    events = "\n".join(f"- {event.created_at:%Y-%m-%d %H:%M}: {event.body}" for event in incident.events) or "- No events"
    return (
        f"{incident.reference}\n"
        f"Title: {incident.title}\n"
        f"Status: {incident.status}\n"
        f"Priority: {incident.priority}\n"
        f"Opened: {incident.opened_at.isoformat()}\n"
        f"Description: {incident.description or 'N/A'}\n"
        f"Resolution notes: {incident.resolution_notes or 'N/A'}\n"
        f"Linked alerts: {linked_alerts}\n"
        f"Timeline:\n{events}\n"
    )
