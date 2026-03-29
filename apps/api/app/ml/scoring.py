from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session

from app.models.entities import Alert, AlertSeverity, IncidentAlertLink, ModelMetadata

MODEL_DIR = Path(__file__).resolve().parent / "runtime"
MODEL_FILE = MODEL_DIR / "alert-risk-model.pkl"

FEATURE_NAMES = [
    "severity_score",
    "criticality",
    "tag_count",
    "open_asset_alerts",
    "is_wazuh",
    "is_suricata",
    "is_nmap",
    "is_hydra",
    "has_auth_signal",
    "has_network_signal",
    "has_exposure_signal",
]


def _severity_to_score(severity: str) -> int:
    return {
        AlertSeverity.CRITICAL.value: 4,
        AlertSeverity.HIGH.value: 3,
        AlertSeverity.MEDIUM.value: 2,
        AlertSeverity.LOW.value: 1,
    }.get(severity, 1)


def extract_features(record: dict[str, Any]) -> dict[str, float]:
    tags = [str(tag).lower() for tag in record.get("tags", [])]
    text = " ".join(
        [
            str(record.get("title", "")).lower(),
            str(record.get("description", "")).lower(),
            " ".join(tags),
        ]
    )
    source = str(record.get("source", "")).lower()
    return {
        "severity_score": float(_severity_to_score(str(record.get("severity", AlertSeverity.LOW.value)))),
        "criticality": float(record.get("asset_criticality", 3)),
        "tag_count": float(len(tags)),
        "open_asset_alerts": float(record.get("open_asset_alerts", 0)),
        "is_wazuh": 1.0 if source == "wazuh" else 0.0,
        "is_suricata": 1.0 if source == "suricata" else 0.0,
        "is_nmap": 1.0 if source == "nmap" else 0.0,
        "is_hydra": 1.0 if source == "hydra" else 0.0,
        "has_auth_signal": 1.0 if any(keyword in text for keyword in ("auth", "credential", "password", "ssh")) else 0.0,
        "has_network_signal": 1.0 if any(keyword in text for keyword in ("dns", "smb", "rdp", "scan", "recon")) else 0.0,
        "has_exposure_signal": 1.0 if any(keyword in text for keyword in ("exposed", "port", "open", "reuse")) else 0.0,
    }


def _default_score(features: dict[str, float]) -> tuple[float, list[dict[str, Any]]]:
    weights = {
        "severity_score": 18,
        "criticality": 10,
        "open_asset_alerts": 4,
        "has_auth_signal": 10,
        "has_network_signal": 8,
        "has_exposure_signal": 8,
        "tag_count": 2,
    }
    raw = sum(features.get(name, 0) * weight for name, weight in weights.items())
    score = float(min(100, max(5, raw)))
    explanations = [
        {"factor": name.replace("_", " "), "impact": round(features.get(name, 0) * weight, 2)}
        for name, weight in sorted(weights.items(), key=lambda item: item[1], reverse=True)
        if features.get(name, 0)
    ]
    return score, explanations[:3]


def _load_pipeline() -> dict[str, Any] | None:
    if not MODEL_FILE.exists():
        return None
    with MODEL_FILE.open("rb") as handle:
        return pickle.load(handle)


def score_alert(record: dict[str, Any]) -> tuple[float, list[dict[str, Any]], str]:
    features = extract_features(record)
    pipeline_payload = _load_pipeline()
    if pipeline_payload is None:
        score, explanations = _default_score(features)
    else:
        vector = np.array([[features[name] for name in FEATURE_NAMES]])
        probability = pipeline_payload["pipeline"].predict_proba(vector)[0][1]
        score = float(round(probability * 100, 2))
        coefficients = pipeline_payload["pipeline"].named_steps["model"].coef_[0]
        explanations = []
        for name, coefficient in sorted(
            zip(FEATURE_NAMES, coefficients, strict=False),
            key=lambda item: abs(item[1] * features[item[0]]),
            reverse=True,
        ):
            value = features[name]
            if not value:
                continue
            explanations.append(
                {
                    "factor": name.replace("_", " "),
                    "impact": round(float(coefficient * value), 3),
                    "value": value,
                }
            )
        explanations = explanations[:3]

    label = "critical" if score >= 85 else "high" if score >= 65 else "medium" if score >= 35 else "low"
    return score, explanations, label


def _build_training_rows(db: Session) -> tuple[np.ndarray, np.ndarray]:
    alerts = db.query(Alert).all()
    rows: list[list[float]] = []
    labels: list[int] = []

    incident_alert_ids = {item[0] for item in db.query(IncidentAlertLink.alert_id).distinct().all()}

    for alert in alerts:
        features = extract_features(
            {
                "title": alert.title,
                "description": alert.description,
                "source": alert.source,
                "severity": alert.severity,
                "tags": alert.tags,
                "asset_criticality": alert.asset.criticality if alert.asset else 3,
                "open_asset_alerts": len(alert.asset.alerts) if alert.asset else 0,
            }
        )
        rows.append([features[name] for name in FEATURE_NAMES])
        label = 1 if alert.id in incident_alert_ids or alert.severity in {AlertSeverity.CRITICAL, AlertSeverity.HIGH} else 0
        labels.append(label)

    if len(rows) < 12:
        baseline_samples = [
            ([4, 5, 3, 6, 1, 0, 0, 0, 1, 0, 0], 1),
            ([3, 4, 2, 4, 0, 1, 0, 0, 0, 1, 0], 1),
            ([2, 3, 1, 1, 0, 0, 1, 0, 0, 0, 1], 1),
            ([2, 2, 1, 0, 0, 0, 0, 1, 1, 0, 1], 1),
            ([1, 2, 0, 0, 1, 0, 0, 0, 0, 0, 0], 0),
            ([1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0], 0),
            ([2, 2, 1, 0, 0, 1, 0, 0, 0, 1, 0], 0),
            ([1, 3, 0, 0, 0, 0, 1, 0, 0, 0, 0], 0),
        ]
        for sample, label in baseline_samples:
            rows.append(sample)
            labels.append(label)

    if len(set(labels)) < 2:
        rows.extend([[4, 5, 3, 5, 1, 0, 0, 0, 1, 0, 0], [1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0]])
        labels.extend([1, 0])

    return np.array(rows, dtype=float), np.array(labels, dtype=int)


def train_model(db: Session, version: str) -> ModelMetadata:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    X, y = _build_training_rows(db)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(max_iter=500, random_state=42)),
        ]
    )
    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)
    accuracy = float(accuracy_score(y_test, predictions))
    metrics = {"accuracy": round(accuracy, 3), "samples": int(len(X))}

    with MODEL_FILE.open("wb") as handle:
        pickle.dump({"pipeline": pipeline, "feature_names": FEATURE_NAMES, "version": version}, handle)

    db.query(ModelMetadata).update({ModelMetadata.is_active: False})
    metadata = ModelMetadata(
        model_name="alert-risk-prioritizer",
        version=version,
        metrics=metrics,
        feature_names=FEATURE_NAMES,
        notes="Logistic regression prioritizer trained from defensive alert history.",
        is_active=True,
    )
    db.add(metadata)
    db.commit()
    db.refresh(metadata)
    return metadata
