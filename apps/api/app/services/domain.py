from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from io import StringIO

from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from app.ml.scoring import AlertRiskAssessment, score_alert
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
    LogEntry,
    ResponseRecommendation,
    User,
)
from app.schemas.domain import (
    DashboardActivityItem,
    DashboardKpi,
    DashboardSummary,
    DashboardTrendPoint,
    ResponseActionResult,
)
from app.services.audit import record_audit
from app.services.realtime import manager


def ensure_asset(
    db: Session,
    *,
    hostname: str,
    ip_address: str | None = None,
    operating_system: str | None = None,
    criticality: int = 3,
) -> Asset:
    asset = db.query(Asset).filter(Asset.hostname == hostname).one_or_none() if hostname else None
    if asset is None and ip_address:
        asset = db.query(Asset).filter(Asset.ip_address == ip_address).one_or_none()
    if asset is None:
        asset = Asset(
            hostname=hostname or ip_address or "unknown-asset",
            ip_address=ip_address,
            operating_system=operating_system,
            criticality=criticality,
        )
        db.add(asset)
    else:
        if hostname and asset.hostname != hostname:
            asset.hostname = hostname
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
    alert_count_bonus = min(20, len(open_alerts) * 0.5)
    asset.risk_score = round(min(100, average_score + alert_count_bonus), 2)
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


def _sync_response_recommendations(alert: Alert, items: list[dict[str, str | int | None]]) -> None:
    alert.response_recommendations.clear()
    for item in items:
        alert.response_recommendations.append(
            ResponseRecommendation(
                title=str(item["title"]),
                description=str(item["description"]) if item["description"] else None,
                priority=int(item["priority"]),
            )
        )


def _build_scoring_record(
    *,
    title: str,
    description: str | None,
    source: str,
    source_type: str,
    event_type: str | None,
    severity: str,
    tags: list[str],
    raw_payload: dict,
    parsed_payload: dict,
    occurred_at: datetime | None,
    asset: Asset | None,
) -> dict:
    return {
        "title": title,
        "description": description,
        "source": source,
        "source_type": source_type,
        "event_type": event_type,
        "severity": severity,
        "tags": tags,
        "raw_payload": raw_payload,
        "parsed_payload": parsed_payload,
        "occurred_at": occurred_at or datetime.now(timezone.utc),
        "detected_at": occurred_at or datetime.now(timezone.utc),
        "asset_id": asset.id if asset else None,
        "asset_hostname": asset.hostname if asset else None,
        "asset_ip": asset.ip_address if asset else None,
        "asset_criticality": asset.criticality if asset else 3,
    }


def _apply_alert_risk_assessment(
    db: Session,
    *,
    alert: Alert,
    assessment: AlertRiskAssessment,
    preserve_summary: bool = False,
) -> None:
    alert.risk_score = assessment.score
    alert.risk_label = assessment.band
    alert.explainability = assessment.explanations
    if not preserve_summary or not alert.explanation_summary:
        alert.explanation_summary = assessment.summary
    recommendation_items = _build_recommendations(alert.source, alert.severity, list(alert.tags or []))
    alert.recommendations = [str(item["title"]) for item in recommendation_items]
    _sync_response_recommendations(alert, recommendation_items)
    db.add(alert)


def rescore_alerts(
    db: Session,
    *,
    source: str | None = None,
    open_only: bool = True,
    limit: int | None = None,
) -> dict[str, int | str | None]:
    query = db.query(Alert).options(joinedload(Alert.asset), joinedload(Alert.response_recommendations))
    if source:
        query = query.filter(Alert.source == source)
    if open_only:
        query = query.filter(Alert.status.notin_([AlertStatus.RESOLVED, AlertStatus.SUPPRESSED]))
    query = query.order_by(Alert.detected_at.desc())
    if limit:
        query = query.limit(limit)

    alerts = query.all()
    touched_assets: dict[str, Asset] = {}

    for alert in alerts:
        scoring_record = _build_scoring_record(
            title=alert.title,
            description=alert.description,
            source=alert.source,
            source_type=alert.source_type,
            event_type=alert.event_type,
            severity=alert.severity,
            tags=list(alert.tags or []),
            raw_payload=dict(alert.raw_payload or {}),
            parsed_payload=dict(alert.parsed_payload or {}),
            occurred_at=alert.occurred_at,
            asset=alert.asset,
        )
        assessment = score_alert(scoring_record, db=db, asset=alert.asset, existing_alert_id=alert.id)
        _apply_alert_risk_assessment(db, alert=alert, assessment=assessment, preserve_summary=False)
        if alert.asset:
            touched_assets[alert.asset.id] = alert.asset

    for asset in touched_assets.values():
        _refresh_asset_risk(asset)

    db.commit()
    return {
        "rescored_alerts": len(alerts),
        "updated_assets": len(touched_assets),
    }


async def broadcast_alert_event(alert: Alert, event: str, metadata: dict | None = None) -> None:
    payload = {
        "event": event,
        "alert_id": alert.id,
        "title": alert.title,
        "severity": alert.severity,
        "status": alert.status,
        "risk_score": alert.risk_score,
        "occurred_at": alert.occurred_at.isoformat(),
        "detected_at": alert.detected_at.isoformat(),
    }
    if metadata:
        payload.update(metadata)
    await manager.broadcast("alerts", payload)


def _extract_response_ip(alert: Alert) -> str | None:
    parsed_payload = dict(alert.parsed_payload or {})
    raw_payload = dict(alert.raw_payload or {})
    candidates = [
        parsed_payload.get("src_ip"),
        parsed_payload.get("source_ip"),
        parsed_payload.get("indicator_ip"),
        raw_payload.get("src_ip"),
        raw_payload.get("srcip"),
        raw_payload.get("source_ip"),
        raw_payload.get("ip"),
        alert.asset.ip_address if alert.asset else None,
    ]
    for candidate in candidates:
        if candidate:
            return str(candidate).strip()
    return None


def _extract_response_user(alert: Alert) -> str | None:
    parsed_payload = dict(alert.parsed_payload or {})
    raw_payload = dict(alert.raw_payload or {})
    for container in (parsed_payload, raw_payload):
        for key in ("username", "user", "account", "principal", "target_user", "target_account"):
            value = container.get(key)
            if value:
                return str(value).strip()
    return None


def execute_alert_response(
    db: Session,
    *,
    alert: Alert,
    action: str,
    actor: User,
    ip_address: str | None,
    reason: str | None = None,
) -> tuple[Alert, ResponseActionResult]:
    action_labels = {
        "block_ip": "Block source IP",
        "isolate_asset": "Isolate asset",
        "disable_user": "Disable user",
        "contain_alert": "Contain alert",
    }
    if action not in action_labels:
        raise ValueError("Unsupported response action.")

    target: dict[str, str | None]
    follow_up: list[str]

    if action == "block_ip":
        ip_target = _extract_response_ip(alert)
        if not ip_target:
            raise ValueError("No source IP was found on this alert, so a block action cannot be recorded.")
        target = {
            "ip_address": ip_target,
            "asset_hostname": alert.asset.hostname if alert.asset else None,
        }
        message = (
            f"Recorded a defensive block request for source IP {ip_target}. "
            "This is tracked inside AegisCore for analyst follow-through or future SOAR integration."
        )
        follow_up = [
            "Apply the block in your firewall, Wazuh active response, or upstream gateway.",
            "Validate that new events from this indicator stop after containment.",
        ]
    elif action == "isolate_asset":
        if alert.asset is None:
            raise ValueError("This alert is not mapped to an asset, so host isolation cannot be recorded.")
        target = {
            "hostname": alert.asset.hostname,
            "ip_address": alert.asset.ip_address,
        }
        message = (
            f"Recorded host isolation for {alert.asset.hostname}. "
            "Use your endpoint tooling or lab workflow to disconnect the host from the network."
        )
        follow_up = [
            "Confirm the endpoint is quarantined or otherwise segmented.",
            "Capture volatile evidence before rebooting or reimaging the host.",
        ]
    elif action == "disable_user":
        username = _extract_response_user(alert)
        if not username:
            raise ValueError("No username was found on this alert, so an account disable action cannot be recorded.")
        target = {
            "username": username,
            "asset_hostname": alert.asset.hostname if alert.asset else None,
        }
        message = (
            f"Recorded an account disable request for {username}. "
            "Coordinate with your identity provider or operating system account controls to complete the step."
        )
        follow_up = [
            "Force a credential reset if compromise is suspected.",
            "Review recent authentication events tied to this identity.",
        ]
    else:
        target = {
            "alert_title": alert.title,
            "severity": alert.severity,
        }
        message = "Recorded containment handling for this alert and moved it into the active investigation workflow."
        follow_up = [
            "Assign an analyst owner and document the next investigative step.",
            "Escalate into an incident if the alert remains confirmed or recurring.",
        ]

    if alert.status not in {AlertStatus.RESOLVED, AlertStatus.SUPPRESSED}:
        alert.status = AlertStatus.INVESTIGATING

    alert.recommendations = sorted({*list(alert.recommendations or []), "Review containment outcome"})
    db.add(alert)

    reason_suffix = f" Reason: {reason}" if reason else ""
    db.add(
        AlertComment(
            alert_id=alert.id,
            author_id=actor.id,
            body=f"{action_labels[action]} recorded. {message}{reason_suffix}",
        )
    )
    db.commit()
    db.refresh(alert)

    executed_at = datetime.now(timezone.utc)
    record_audit(
        db,
        actor=actor,
        action="alert.response_executed",
        entity_type="alert",
        entity_id=alert.id,
        details={
            "response_action": action,
            "status": "simulated",
            "target": target,
            "reason": reason,
        },
        ip_address=ip_address,
    )

    return (
        alert,
        ResponseActionResult(
            alert_id=alert.id,
            action=action,
            status="simulated",
            message=message,
            executed_at=executed_at,
            target=target,
            follow_up=follow_up,
        ),
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
    asset = ensure_asset(db, hostname=asset_hostname or asset_ip or "unknown-asset", ip_address=asset_ip) if (asset_hostname or asset_ip) else None
    scoring_record = _build_scoring_record(
        title=title,
        description=description,
        source=source,
        source_type=source_type,
        event_type=event_type,
        severity=severity,
        tags=tags,
        raw_payload=raw_payload,
        parsed_payload=parsed_payload,
        occurred_at=occurred_at,
        asset=asset,
    )
    assessment = score_alert(scoring_record, db=db, asset=asset)

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
        risk_score=assessment.score,
        explainability=assessment.explanations,
        explanation_summary=assessment.summary,
        risk_label=assessment.band,
        recommendations=[],
        occurred_at=occurred_at or datetime.now(timezone.utc),
    )
    db.add(alert)
    db.flush()
    _apply_alert_risk_assessment(db, alert=alert, assessment=assessment)

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


_ALERT_UPDATE_FIELDS = {"status", "severity", "assigned_to_id", "tags", "explanation_summary"}


def update_alert(db: Session, alert: Alert, *, payload: dict, actor: User, ip_address: str | None) -> Alert:
    manual_summary = payload.get("explanation_summary")
    for field, value in payload.items():
        if field not in _ALERT_UPDATE_FIELDS:
            continue
        if value is None and field != "assigned_to_id":
            continue
        setattr(alert, field, value)
    scoring_record = _build_scoring_record(
        title=alert.title,
        description=alert.description,
        source=alert.source,
        source_type=alert.source_type,
        event_type=alert.event_type,
        severity=alert.severity,
        tags=list(alert.tags or []),
        raw_payload=dict(alert.raw_payload or {}),
        parsed_payload=dict(alert.parsed_payload or {}),
        occurred_at=alert.occurred_at,
        asset=alert.asset,
    )
    assessment = score_alert(scoring_record, db=db, asset=alert.asset, existing_alert_id=alert.id)
    _apply_alert_risk_assessment(db, alert=alert, assessment=assessment, preserve_summary=bool(manual_summary))
    if manual_summary:
        alert.explanation_summary = manual_summary
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