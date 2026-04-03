from __future__ import annotations

import pickle
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.entities import Alert, AlertSeverity, AlertStatus, Asset, IncidentAlertLink, ModelMetadata

MODEL_DIR = Path(__file__).resolve().parent / "runtime"
MODEL_FILE = MODEL_DIR / "alert-risk-model.pkl"
MODEL_ARTIFACT_VERSION = "2026.03.aegiscore-alert-prioritizer.v2"
FEATURE_VERSION = "2026.03.aegiscore-alert-priority.v2"

FEATURE_NAMES = [
    "severity_score",
    "source_type_endpoint",
    "source_type_network",
    "source_type_identity",
    "source_type_lab",
    "source_wazuh",
    "source_suricata",
    "source_nmap",
    "source_hydra",
    "event_authentication",
    "event_network",
    "event_exposure",
    "event_malware",
    "frequency_1h",
    "recurrence_24h",
    "recurrence_7d",
    "asset_criticality",
    "open_asset_alerts",
    "correlated_sources_24h",
    "incident_history_30d",
    "user_sensitivity",
    "source_spike_ratio",
    "off_hours_activity",
    "lab_imported",
]

OPEN_ALERT_STATUSES = {AlertStatus.OPEN.value, AlertStatus.TRIAGED.value, AlertStatus.INVESTIGATING.value}
SOURCE_TYPE_ENDPOINTS = {"endpoint", "host", "agent"}
SOURCE_TYPE_NETWORKS = {"network", "ids", "nids", "sensor"}
SOURCE_TYPE_IDENTITIES = {"identity", "authentication", "iam"}
SOURCE_TYPE_LAB = {"lab-import", "lab", "import"}


@dataclass(slots=True)
class AlertRiskAssessment:
    score: float
    band: str
    explanations: list[dict[str, Any]]
    summary: str
    features: dict[str, float]
    model_components: dict[str, float]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return _utcnow()


def _clean_text(value: Any) -> str:
    return str(value or "").strip().lower()


def _severity_to_score(severity: str) -> int:
    return {
        AlertSeverity.CRITICAL.value: 4,
        AlertSeverity.HIGH.value: 3,
        AlertSeverity.MEDIUM.value: 2,
        AlertSeverity.LOW.value: 1,
    }.get(str(severity).lower(), 1)


def _normalize_source_type(source_type: str, source: str, lab_imported: bool) -> str:
    normalized = source_type.strip().lower() if source_type else "telemetry"
    if lab_imported or source in {"nmap", "hydra"}:
        return "lab-import"
    if normalized in SOURCE_TYPE_ENDPOINTS:
        return "endpoint"
    if normalized in SOURCE_TYPE_NETWORKS:
        return "network"
    if normalized in SOURCE_TYPE_IDENTITIES:
        return "identity"
    if normalized in SOURCE_TYPE_LAB:
        return "lab-import"
    return normalized or "telemetry"


def _combined_signal_text(record: dict[str, Any], tags: list[str]) -> str:
    parsed_payload = record.get("parsed_payload") or {}
    return " ".join(
        [
            _clean_text(record.get("title")),
            _clean_text(record.get("description")),
            _clean_text(record.get("event_type")),
            _clean_text(parsed_payload.get("message")),
            _clean_text(parsed_payload.get("category")),
            _clean_text(parsed_payload.get("signature")),
            " ".join(tags),
        ]
    )


def _event_flags(text: str) -> dict[str, float]:
    auth_terms = ("auth", "login", "credential", "password", "ssh", "kerberos", "failed", "account", "hydra")
    network_terms = ("network", "dns", "smb", "rdp", "tls", "http", "portscan", "traffic", "suricata")
    exposure_terms = ("exposed", "port", "service", "open", "exposure", "scan", "nmap")
    malware_terms = ("malware", "trojan", "ransom", "beacon", "payload", "c2", "command-and-control")
    return {
        "event_authentication": 1.0 if any(term in text for term in auth_terms) else 0.0,
        "event_network": 1.0 if any(term in text for term in network_terms) else 0.0,
        "event_exposure": 1.0 if any(term in text for term in exposure_terms) else 0.0,
        "event_malware": 1.0 if any(term in text for term in malware_terms) else 0.0,
    }


def _extract_username(record: dict[str, Any]) -> str | None:
    parsed_payload = record.get("parsed_payload") or {}
    raw_payload = record.get("raw_payload") or {}
    for container in (parsed_payload, raw_payload):
        for key in ("username", "user", "account", "principal", "target_user", "target_account"):
            value = container.get(key)
            if value:
                return str(value).strip().lower()
    return None


def _derive_user_sensitivity(record: dict[str, Any], text: str, username: str | None) -> float:
    parsed_payload = record.get("parsed_payload") or {}
    explicit = parsed_payload.get("user_sensitivity")
    if explicit is not None:
        try:
            return float(max(1, min(5, int(explicit))))
        except (TypeError, ValueError):
            pass

    candidate_text = " ".join(filter(None, [username, text]))
    if any(term in candidate_text for term in ("domain admin", "admin", "root", "administrator", "privileged")):
        return 5.0
    if any(term in candidate_text for term in ("finance", "payroll", "hr", "executive", "ceo", "cfo")):
        return 4.0
    if any(term in candidate_text for term in ("service", "svc_", "backup", "monitoring")):
        return 3.0
    if username:
        return 2.0
    return 1.0


def _exclude_existing_alert(query, existing_alert_id: str | None):
    if existing_alert_id:
        return query.filter(Alert.id != existing_alert_id)
    return query


def _count_matching_alerts(
    db: Session,
    *,
    since: datetime,
    source: str | None = None,
    asset_id: str | None = None,
    event_type: str | None = None,
    title: str | None = None,
    existing_alert_id: str | None = None,
) -> int:
    query = db.query(func.count(Alert.id)).filter(Alert.detected_at >= since)
    if source:
        query = query.filter(Alert.source == source)
    if asset_id:
        query = query.filter(Alert.asset_id == asset_id)
    if event_type:
        query = query.filter(Alert.event_type == event_type)
    elif title:
        query = query.filter(Alert.title == title)
    query = _exclude_existing_alert(query, existing_alert_id)
    return int(query.scalar() or 0)


def _count_open_asset_alerts(db: Session, *, asset_id: str | None, existing_alert_id: str | None) -> int:
    if not asset_id:
        return 0
    query = db.query(func.count(Alert.id)).filter(
        Alert.asset_id == asset_id,
        Alert.status.in_(list(OPEN_ALERT_STATUSES)),
    )
    query = _exclude_existing_alert(query, existing_alert_id)
    return int(query.scalar() or 0)


def _count_correlated_sources(db: Session, *, asset_id: str | None, since: datetime, existing_alert_id: str | None) -> int:
    if not asset_id:
        return 0
    query = db.query(func.count(func.distinct(Alert.source))).filter(Alert.asset_id == asset_id, Alert.detected_at >= since)
    query = _exclude_existing_alert(query, existing_alert_id)
    return int(query.scalar() or 0)


def _count_incident_history(db: Session, *, asset_id: str | None, since: datetime, existing_alert_id: str | None) -> int:
    if not asset_id:
        return 0
    query = (
        db.query(func.count(IncidentAlertLink.id))
        .join(Alert, IncidentAlertLink.alert_id == Alert.id)
        .filter(Alert.asset_id == asset_id, Alert.detected_at >= since)
    )
    query = _exclude_existing_alert(query, existing_alert_id)
    return int(query.scalar() or 0)


def extract_features(
    record: dict[str, Any],
    *,
    db: Session | None = None,
    asset: Asset | None = None,
    existing_alert_id: str | None = None,
) -> dict[str, float]:
    occurred_at = _coerce_datetime(record.get("occurred_at") or record.get("detected_at"))
    source = _clean_text(record.get("source"))
    tags = [_clean_text(tag) for tag in record.get("tags", []) if _clean_text(tag)]
    parsed_payload = dict(record.get("parsed_payload") or {})
    raw_payload = dict(record.get("raw_payload") or {})
    lab_imported = bool(parsed_payload.get("lab_imported") or raw_payload.get("lab_imported") or source in {"nmap", "hydra"})
    source_type = _normalize_source_type(_clean_text(record.get("source_type") or "telemetry"), source, lab_imported)
    event_type = _clean_text(record.get("event_type"))
    text = _combined_signal_text(record, tags)
    event_flags = _event_flags(text)
    username = _extract_username(record)

    asset_id = str(record.get("asset_id")) if record.get("asset_id") else (asset.id if asset else None)
    asset_criticality = float(record.get("asset_criticality") or (asset.criticality if asset else 3))
    severity_score = float(_severity_to_score(str(record.get("severity", AlertSeverity.LOW.value)).lower()))

    frequency_1h = 0
    recurrence_24h = 0
    recurrence_7d = 0
    open_asset_alerts = 0
    correlated_sources_24h = 0
    incident_history_30d = 0
    source_spike_ratio = 1.0

    if db is not None and source:
        frequency_1h = _count_matching_alerts(
            db,
            since=occurred_at - timedelta(hours=1),
            source=source,
            existing_alert_id=existing_alert_id,
        )
        recurrence_24h = _count_matching_alerts(
            db,
            since=occurred_at - timedelta(hours=24),
            source=source,
            asset_id=asset_id,
            event_type=event_type or None,
            title=str(record.get("title") or "") or None,
            existing_alert_id=existing_alert_id,
        )
        recurrence_7d = _count_matching_alerts(
            db,
            since=occurred_at - timedelta(days=7),
            source=source,
            asset_id=asset_id,
            event_type=event_type or None,
            title=str(record.get("title") or "") or None,
            existing_alert_id=existing_alert_id,
        )
        open_asset_alerts = _count_open_asset_alerts(db, asset_id=asset_id, existing_alert_id=existing_alert_id)
        correlated_sources_24h = _count_correlated_sources(
            db,
            asset_id=asset_id,
            since=occurred_at - timedelta(hours=24),
            existing_alert_id=existing_alert_id,
        )
        incident_history_30d = _count_incident_history(
            db,
            asset_id=asset_id,
            since=occurred_at - timedelta(days=30),
            existing_alert_id=existing_alert_id,
        )
        source_frequency_7d = _count_matching_alerts(
            db,
            since=occurred_at - timedelta(days=7),
            source=source,
            existing_alert_id=existing_alert_id,
        )
        baseline_per_hour = max(source_frequency_7d / (7 * 24), 0.5)
        source_spike_ratio = float(min(10.0, frequency_1h / baseline_per_hour if baseline_per_hour else frequency_1h))

    off_hours = 1.0 if occurred_at.hour < 6 or occurred_at.hour >= 20 else 0.0
    user_sensitivity = _derive_user_sensitivity(record, text, username)

    return {
        "severity_score": severity_score,
        "source_type_endpoint": 1.0 if source_type == "endpoint" else 0.0,
        "source_type_network": 1.0 if source_type == "network" else 0.0,
        "source_type_identity": 1.0 if source_type == "identity" else 0.0,
        "source_type_lab": 1.0 if source_type == "lab-import" else 0.0,
        "source_wazuh": 1.0 if source == "wazuh" else 0.0,
        "source_suricata": 1.0 if source == "suricata" else 0.0,
        "source_nmap": 1.0 if source == "nmap" else 0.0,
        "source_hydra": 1.0 if source == "hydra" else 0.0,
        **event_flags,
        "frequency_1h": float(frequency_1h),
        "recurrence_24h": float(recurrence_24h),
        "recurrence_7d": float(recurrence_7d),
        "asset_criticality": asset_criticality,
        "open_asset_alerts": float(open_asset_alerts),
        "correlated_sources_24h": float(correlated_sources_24h),
        "incident_history_30d": float(incident_history_30d),
        "user_sensitivity": float(user_sensitivity),
        "source_spike_ratio": float(source_spike_ratio),
        "off_hours_activity": off_hours,
        "lab_imported": 1.0 if lab_imported else 0.0,
    }


def _baseline_row(label: int, **overrides: float) -> dict[str, float]:
    row = {name: 0.0 for name in FEATURE_NAMES}
    row.update(
        {
            "severity_score": 1.0,
            "asset_criticality": 2.0,
            "source_spike_ratio": 1.0,
        }
    )
    row.update(overrides)
    row["label"] = float(label)
    return row


def _baseline_training_frame() -> pd.DataFrame:
    rows = [
        _baseline_row(
            1,
            severity_score=4.0,
            source_type_endpoint=1.0,
            source_wazuh=1.0,
            event_authentication=1.0,
            frequency_1h=6.0,
            recurrence_24h=8.0,
            recurrence_7d=15.0,
            asset_criticality=5.0,
            open_asset_alerts=5.0,
            correlated_sources_24h=3.0,
            incident_history_30d=2.0,
            user_sensitivity=4.0,
            source_spike_ratio=6.0,
            off_hours_activity=1.0,
        ),
        _baseline_row(
            1,
            severity_score=4.0,
            source_type_network=1.0,
            source_suricata=1.0,
            event_network=1.0,
            event_malware=1.0,
            frequency_1h=4.0,
            recurrence_24h=5.0,
            recurrence_7d=9.0,
            asset_criticality=5.0,
            open_asset_alerts=4.0,
            correlated_sources_24h=2.0,
            incident_history_30d=1.0,
            user_sensitivity=3.0,
            source_spike_ratio=4.0,
        ),
        _baseline_row(
            1,
            severity_score=3.0,
            source_type_lab=1.0,
            source_nmap=1.0,
            event_exposure=1.0,
            frequency_1h=2.0,
            recurrence_24h=3.0,
            recurrence_7d=6.0,
            asset_criticality=4.0,
            open_asset_alerts=2.0,
            correlated_sources_24h=2.0,
            incident_history_30d=1.0,
            user_sensitivity=2.0,
            source_spike_ratio=2.5,
            lab_imported=1.0,
        ),
        _baseline_row(
            1,
            severity_score=3.0,
            source_type_identity=1.0,
            source_hydra=1.0,
            event_authentication=1.0,
            event_exposure=1.0,
            frequency_1h=3.0,
            recurrence_24h=5.0,
            recurrence_7d=7.0,
            asset_criticality=4.0,
            open_asset_alerts=3.0,
            correlated_sources_24h=2.0,
            incident_history_30d=1.0,
            user_sensitivity=5.0,
            source_spike_ratio=3.0,
            off_hours_activity=1.0,
            lab_imported=1.0,
        ),
        _baseline_row(
            0,
            severity_score=1.0,
            source_type_endpoint=1.0,
            source_wazuh=1.0,
            frequency_1h=0.0,
            recurrence_24h=0.0,
            recurrence_7d=1.0,
            asset_criticality=2.0,
            open_asset_alerts=0.0,
            correlated_sources_24h=1.0,
            incident_history_30d=0.0,
            user_sensitivity=1.0,
            source_spike_ratio=1.0,
        ),
        _baseline_row(
            0,
            severity_score=1.0,
            source_type_network=1.0,
            source_suricata=1.0,
            event_network=1.0,
            frequency_1h=1.0,
            recurrence_24h=1.0,
            recurrence_7d=1.0,
            asset_criticality=2.0,
            open_asset_alerts=0.0,
            correlated_sources_24h=1.0,
            incident_history_30d=0.0,
            user_sensitivity=1.0,
            source_spike_ratio=1.2,
        ),
        _baseline_row(
            0,
            severity_score=2.0,
            source_type_lab=1.0,
            source_nmap=1.0,
            event_exposure=1.0,
            frequency_1h=0.0,
            recurrence_24h=1.0,
            recurrence_7d=1.0,
            asset_criticality=2.0,
            open_asset_alerts=1.0,
            correlated_sources_24h=1.0,
            incident_history_30d=0.0,
            user_sensitivity=1.0,
            source_spike_ratio=1.0,
            lab_imported=1.0,
        ),
        _baseline_row(
            0,
            severity_score=1.0,
            source_type_identity=1.0,
            source_hydra=1.0,
            event_authentication=1.0,
            frequency_1h=1.0,
            recurrence_24h=1.0,
            recurrence_7d=2.0,
            asset_criticality=2.0,
            open_asset_alerts=0.0,
            correlated_sources_24h=1.0,
            incident_history_30d=0.0,
            user_sensitivity=2.0,
            source_spike_ratio=1.3,
            lab_imported=1.0,
        ),
    ]
    return pd.DataFrame(rows)


def _build_training_frame(db: Session) -> pd.DataFrame:
    # Eager-load relationships in one query to avoid N+1 during feature extraction.
    # We pass db=None to extract_features so no per-alert COUNT queries fire;
    # temporal frequency features default to 0 which is acceptable for training
    # because the label is derived from severity, incident linkage, and status —
    # not from frequency counts.
    alerts = (
        db.query(Alert)
        .options(
            joinedload(Alert.asset),
            joinedload(Alert.incident_links),
        )
        .all()
    )
    rows: list[dict[str, float]] = []

    for alert in alerts:
        asset_criticality = alert.asset.criticality if alert.asset else 3
        feature_row = extract_features(
            {
                "title": alert.title,
                "description": alert.description,
                "source": alert.source,
                "source_type": alert.source_type,
                "event_type": alert.event_type,
                "severity": alert.severity,
                "tags": alert.tags,
                "parsed_payload": alert.parsed_payload,
                "raw_payload": alert.raw_payload,
                "occurred_at": alert.occurred_at,
                "detected_at": alert.detected_at,
                "asset_id": alert.asset_id,
                "asset_criticality": asset_criticality,
            },
            db=None,  # no per-alert DB queries during batch training
            asset=alert.asset,
            existing_alert_id=alert.id,
        )
        high_risk_label = (
            bool(alert.incident_links)
            or alert.status == AlertStatus.INVESTIGATING
            or alert.severity in {AlertSeverity.CRITICAL.value, AlertSeverity.HIGH.value}
            or asset_criticality >= 4
        )
        rows.append({**feature_row, "label": float(1 if high_risk_label else 0)})

    frame = pd.DataFrame(rows)
    baseline = _baseline_training_frame()
    if frame.empty:
        frame = baseline
    else:
        frame = pd.concat([frame, baseline], ignore_index=True)

    for feature_name in FEATURE_NAMES:
        if feature_name not in frame.columns:
            frame[feature_name] = 0.0
    frame["label"] = frame["label"].astype(int)
    return frame


def _default_score(features: dict[str, float]) -> tuple[float, dict[str, float]]:
    weighted_total = (
        features["severity_score"] * 11
        + features["asset_criticality"] * 6
        + min(features["frequency_1h"], 6) * 4
        + min(features["recurrence_24h"], 6) * 5
        + min(features["correlated_sources_24h"], 4) * 6
        + min(features["open_asset_alerts"], 8) * 3
        + min(features["incident_history_30d"], 4) * 4
        + features["user_sensitivity"] * 4
        + min(features["source_spike_ratio"], 6) * 5
        + features["event_authentication"] * 7
        + features["event_network"] * 4
        + features["event_exposure"] * 5
        + features["event_malware"] * 9
        + features["off_hours_activity"] * 3
    )
    if features["lab_imported"]:
        weighted_total *= 0.92
    score = float(np.clip(weighted_total, 5, 100))
    return score, {"heuristic_score": round(score, 2), "classifier_probability": round(score / 100, 4), "anomaly_score": 0.0}


def _risk_band(score: float) -> str:
    if score >= 85:
        return "critical"
    if score >= 65:
        return "high"
    if score >= 35:
        return "medium"
    return "low"


def _load_pipeline() -> dict[str, Any] | None:
    if not MODEL_FILE.exists():
        return None
    try:
        with MODEL_FILE.open("rb") as handle:
            payload = pickle.load(handle)
    except Exception:
        return None
    required_keys = {"artifact_version", "classifier", "anomaly_model", "anomaly_scaler", "anomaly_bounds", "feature_names"}
    if not required_keys.issubset(payload) or payload.get("artifact_version") != MODEL_ARTIFACT_VERSION:
        return None
    return payload


def _model_score(features: dict[str, float], artifact: dict[str, Any]) -> tuple[float, dict[str, float]]:
    frame = pd.DataFrame([{name: features[name] for name in FEATURE_NAMES}], columns=FEATURE_NAMES)
    X = frame[FEATURE_NAMES].to_numpy(dtype=float)
    classifier: Pipeline = artifact["classifier"]
    anomaly_scaler: StandardScaler = artifact["anomaly_scaler"]
    anomaly_model: IsolationForest = artifact["anomaly_model"]

    classifier_probability = float(classifier.predict_proba(X)[0][1])
    heuristic_score, _ = _default_score(features)
    scaled = anomaly_scaler.transform(X)
    decision = float(anomaly_model.decision_function(scaled)[0])
    bounds = artifact.get("anomaly_bounds", {})
    min_value = float(bounds.get("min", -0.2))
    max_value = float(bounds.get("max", 0.2))
    spread = max(max_value - min_value, 1e-6)
    anomaly_score = float(np.clip(1 - ((decision - min_value) / spread), 0, 1))

    final_probability = float(
        np.clip((heuristic_score / 100) * 0.45 + classifier_probability * 0.4 + anomaly_score * 0.15, 0, 1)
    )
    return round(final_probability * 100, 2), {
        "heuristic_score": round(heuristic_score, 2),
        "classifier_probability": round(classifier_probability, 4),
        "anomaly_score": round(anomaly_score, 4),
    }


def _build_explanations(
    record: dict[str, Any],
    features: dict[str, float],
    model_components: dict[str, float],
) -> list[dict[str, Any]]:
    explanations: list[dict[str, Any]] = []
    title = record.get("title") or "this alert"
    hostname = (
        record.get("asset_hostname")
        or (record.get("asset").hostname if isinstance(record.get("asset"), Asset) else None)
        or "the linked asset"
    )

    if features["severity_score"] >= 3:
        explanations.append(
            {
                "factor": "elevated_severity",
                "label": "Elevated severity classification",
                "detail": f"{title} arrived with {record.get('severity', 'unknown')} severity metadata.",
                "impact": round(features["severity_score"] * 5.5, 2),
                "value": features["severity_score"],
                "category": "severity",
            }
        )
    if features["event_authentication"] and (features["frequency_1h"] >= 3 or features["recurrence_24h"] >= 3):
        explanations.append(
            {
                "factor": "repeated_failures_short_window",
                "label": "Repeated failures in short time window",
                "detail": f"{int(features['recurrence_24h'])} similar authentication signals were seen for {hostname} in the last 24 hours.",
                "impact": round(min(24.0, features["recurrence_24h"] * 4.5), 2),
                "value": features["recurrence_24h"],
                "category": "frequency",
            }
        )
    if features["asset_criticality"] >= 4:
        explanations.append(
            {
                "factor": "high_value_asset_involved",
                "label": "High-value asset involved",
                "detail": f"{hostname} is marked as a high-criticality asset in the inventory.",
                "impact": round(features["asset_criticality"] * 4.0, 2),
                "value": features["asset_criticality"],
                "category": "asset",
            }
        )
    if features["correlated_sources_24h"] >= 2:
        explanations.append(
            {
                "factor": "multiple_correlated_sources",
                "label": "Multiple correlated sources",
                "detail": f"{int(features['correlated_sources_24h'])} distinct telemetry sources recently raised signals on {hostname}.",
                "impact": round(min(18.0, features["correlated_sources_24h"] * 5.0), 2),
                "value": features["correlated_sources_24h"],
                "category": "correlation",
            }
        )
    if features["source_spike_ratio"] >= 2.5 or model_components["anomaly_score"] >= 0.55:
        explanations.append(
            {
                "factor": "unusual_source_behavior",
                "label": "Unusual source behavior",
                "detail": "Recent activity is elevated compared with the recent source baseline and anomaly model.",
                "impact": round(max(features["source_spike_ratio"] * 2.5, model_components["anomaly_score"] * 20), 2),
                "value": round(max(features["source_spike_ratio"], model_components["anomaly_score"]), 2),
                "category": "anomaly",
            }
        )
    if features["user_sensitivity"] >= 4:
        explanations.append(
            {
                "factor": "sensitive_user_context",
                "label": "Sensitive user context",
                "detail": "The linked account context looks privileged or business-sensitive.",
                "impact": round(features["user_sensitivity"] * 3.5, 2),
                "value": features["user_sensitivity"],
                "category": "identity",
            }
        )
    if features["incident_history_30d"] >= 1:
        explanations.append(
            {
                "factor": "historical_incident_context",
                "label": "Historical incident context",
                "detail": f"{hostname} already has incident-linked alert history in the past 30 days.",
                "impact": round(min(14.0, features["incident_history_30d"] * 4.0), 2),
                "value": features["incident_history_30d"],
                "category": "history",
            }
        )
    if features["lab_imported"] and features["event_exposure"]:
        explanations.append(
            {
                "factor": "lab_imported_exposure_signal",
                "label": "Lab-imported exposure signal",
                "detail": "Imported Nmap or Hydra findings suggest exposure that should be reviewed in context.",
                "impact": 6.0,
                "value": 1.0,
                "category": "lab",
            }
        )

    if not explanations:
        explanations.append(
            {
                "factor": "baseline_triage_context",
                "label": "Baseline triage context",
                "detail": "The score was assigned from the available alert metadata, severity, and limited historical context.",
                "impact": round(model_components["heuristic_score"] / 10, 2),
                "value": round(model_components["classifier_probability"] * 100, 2),
                "category": "baseline",
            }
        )

    explanations.sort(key=lambda item: abs(float(item["impact"])), reverse=True)
    return explanations[:5]


def _build_summary(score: float, band: str, explanations: list[dict[str, Any]]) -> str:
    if not explanations:
        return f"Assigned {band} risk with limited contextual evidence."
    labels = ", ".join(str(item["label"]).lower() for item in explanations[:3])
    return f"Assigned {band} risk ({score:.1f}/100) because of {labels}."


def score_alert(
    record: dict[str, Any],
    *,
    db: Session | None = None,
    asset: Asset | None = None,
    existing_alert_id: str | None = None,
) -> AlertRiskAssessment:
    features = extract_features(record, db=db, asset=asset, existing_alert_id=existing_alert_id)
    artifact = _load_pipeline()
    if artifact is None:
        score, model_components = _default_score(features)
    else:
        score, model_components = _model_score(features, artifact)

    band = _risk_band(score)
    explanations = _build_explanations(record, features, model_components)
    summary = _build_summary(score, band, explanations)
    return AlertRiskAssessment(
        score=score,
        band=band,
        explanations=explanations,
        summary=summary,
        features=features,
        model_components=model_components,
    )


def _fit_models(X_train: np.ndarray, y_train: np.ndarray) -> tuple[Pipeline, StandardScaler, IsolationForest]:
    classifier = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(max_iter=500, random_state=42)),
        ]
    )
    classifier.fit(X_train, y_train)

    anomaly_scaler = StandardScaler()
    scaled_train = anomaly_scaler.fit_transform(X_train)
    anomaly_model = IsolationForest(contamination=0.2, n_estimators=150, random_state=42)
    anomaly_model.fit(scaled_train)
    return classifier, anomaly_scaler, anomaly_model


def train_model(db: Session, version: str) -> ModelMetadata:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    frame = _build_training_frame(db)
    X = frame[FEATURE_NAMES].to_numpy(dtype=float)
    y = frame["label"].to_numpy(dtype=int)

    label_counts = frame["label"].value_counts().to_dict()
    stratify_labels = y if min(label_counts.values(), default=0) >= 2 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.3,
        random_state=42,
        stratify=stratify_labels,
    )

    classifier, anomaly_scaler, anomaly_model = _fit_models(X_train, y_train)
    predictions = classifier.predict(X_test)
    probabilities = classifier.predict_proba(X_test)[:, 1]

    scaled_train = anomaly_scaler.transform(X_train)
    anomaly_decisions = anomaly_model.decision_function(scaled_train)
    anomaly_bounds = {
        "min": float(np.min(anomaly_decisions)),
        "max": float(np.max(anomaly_decisions)),
        "median": float(np.median(anomaly_decisions)),
    }

    metrics = {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 3),
        "precision": round(float(precision_score(y_test, predictions, zero_division=0)), 3),
        "recall": round(float(recall_score(y_test, predictions, zero_division=0)), 3),
        "f1": round(float(f1_score(y_test, predictions, zero_division=0)), 3),
        "samples": int(len(frame)),
        "positive_rate": round(float(frame["label"].mean()), 3),
    }
    if len(set(y_test.tolist())) > 1:
        metrics["roc_auc"] = round(float(roc_auc_score(y_test, probabilities)), 3)

    with MODEL_FILE.open("wb") as handle:
        pickle.dump(
            {
                "artifact_version": MODEL_ARTIFACT_VERSION,
                "version": version,
                "feature_version": FEATURE_VERSION,
                "feature_names": FEATURE_NAMES,
                "classifier": classifier,
                "anomaly_scaler": anomaly_scaler,
                "anomaly_model": anomaly_model,
                "anomaly_bounds": anomaly_bounds,
            },
            handle,
        )

    performance_notes = [
        "Scores blend a logistic classifier with anomaly pressure and rule-based triage weighting.",
        "Labels are bootstrapped from incident linkage, severity, and recurring multi-source context for demo realism.",
        "This is analyst-assist prioritization only and does not automate response actions.",
    ]

    db.query(ModelMetadata).update({ModelMetadata.is_active: False})
    metadata = ModelMetadata(
        model_name="alert-risk-prioritizer",
        version=version,
        metrics=metrics,
        feature_names=FEATURE_NAMES,
        training_parameters={
            "feature_version": FEATURE_VERSION,
            "classifier": "LogisticRegression",
            "anomaly_model": "IsolationForest",
            "blend_weights": {"heuristic": 0.45, "classifier": 0.4, "anomaly": 0.15},
            "random_state": 42,
            "performance_notes": performance_notes,
        },
        notes="AI-assisted risk scoring for defensive SOC triage. Explanations remain human-readable for analyst review.",
        is_active=True,
    )
    db.add(metadata)
    db.commit()
    db.refresh(metadata)
    return metadata


def build_risk_overview(db: Session) -> dict[str, Any]:
    alerts = (
        db.query(Alert)
        .filter(Alert.status.in_(list(OPEN_ALERT_STATUSES)))
        .order_by(Alert.detected_at.desc())
        .all()
    )
    model = db.query(ModelMetadata).filter(ModelMetadata.is_active.is_(True)).order_by(ModelMetadata.trained_at.desc()).first()

    if not alerts:
        return {
            "active_model": model,
            "summary": {
                "total_alerts": 0,
                "average_risk_score": 0.0,
                "high_priority_alerts": 0,
                "anomalous_alerts": 0,
                "correlated_source_alerts": 0,
            },
            "risk_distribution": [],
            "source_comparison": [],
            "top_explanations": [],
            "anomaly_trend": [],
        }

    rows: list[dict[str, Any]] = []
    explanation_rows: list[dict[str, Any]] = []
    for alert in alerts:
        factor_names = [str(item.get("factor")) for item in alert.explainability or []]
        rows.append(
            {
                "id": alert.id,
                "source": alert.source,
                "risk_score": alert.risk_score,
                "risk_band": alert.risk_label or _risk_band(alert.risk_score),
                "date": alert.detected_at.date().isoformat(),
                "is_anomalous": 1 if "unusual_source_behavior" in factor_names else 0,
                "is_correlated": 1 if "multiple_correlated_sources" in factor_names else 0,
                "is_critical": 1 if (alert.risk_label or _risk_band(alert.risk_score)) == "critical" else 0,
            }
        )
        for factor in alert.explainability or []:
            explanation_rows.append(
                {
                    "factor": str(factor.get("factor")),
                    "label": str(factor.get("label") or factor.get("factor")),
                    "impact": float(abs(factor.get("impact", 0))),
                }
            )

    frame = pd.DataFrame(rows)
    summary = {
        "total_alerts": int(len(frame)),
        "average_risk_score": round(float(frame["risk_score"].mean()), 2),
        "high_priority_alerts": int((frame["risk_score"] >= 65).sum()),
        "anomalous_alerts": int(frame["is_anomalous"].sum()),
        "correlated_source_alerts": int(frame["is_correlated"].sum()),
    }

    distribution_order = ["low", "medium", "high", "critical"]
    risk_distribution = []
    for band in distribution_order:
        count = int((frame["risk_band"] == band).sum())
        if count:
            risk_distribution.append({"band": band, "count": count})

    source_group = frame.groupby("source", as_index=False).agg(
        alert_count=("id", "count"),
        average_risk_score=("risk_score", "mean"),
        anomalous_alerts=("is_anomalous", "sum"),
    )
    source_group["average_risk_score"] = source_group["average_risk_score"].round(2)
    source_comparison = source_group.sort_values("average_risk_score", ascending=False).to_dict(orient="records")

    if explanation_rows:
        explanation_frame = pd.DataFrame(explanation_rows)
        top_explanations_frame = (
            explanation_frame.groupby(["factor", "label"], as_index=False)
            .agg(total_impact=("impact", "sum"), alert_count=("factor", "count"))
            .sort_values(["total_impact", "alert_count"], ascending=False)
            .head(8)
        )
        top_explanations_frame["total_impact"] = top_explanations_frame["total_impact"].round(2)
        top_explanations = top_explanations_frame.to_dict(orient="records")
    else:
        top_explanations = []

    trend_rows = []
    for day in pd.date_range(end=_utcnow().date(), periods=7, freq="D"):
        label = day.date().isoformat()
        day_frame = frame[frame["date"] == label]
        trend_rows.append(
            {
                "label": label,
                "average_risk_score": round(float(day_frame["risk_score"].mean()), 2) if not day_frame.empty else 0.0,
                "anomalous_alerts": int(day_frame["is_anomalous"].sum()) if not day_frame.empty else 0,
                "critical_alerts": int(day_frame["is_critical"].sum()) if not day_frame.empty else 0,
            }
        )

    return {
        "active_model": model,
        "summary": summary,
        "risk_distribution": risk_distribution,
        "source_comparison": source_comparison,
        "top_explanations": top_explanations,
        "anomaly_trend": trend_rows,
    }
