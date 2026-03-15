from __future__ import annotations

from collections import Counter
from typing import Any

from app.ml.anomaly import anomaly_detector
from app.services.mock_store import DEMO_ALERTS


def _alert_counters(reference_alerts: list[dict]) -> tuple[Counter, Counter]:
    source_counter = Counter(str(alert.get("source") or "unknown-source") for alert in reference_alerts)
    tool_counter = Counter(str(alert.get("source_tool") or "other") for alert in reference_alerts)
    return source_counter, tool_counter


def _build_event_context(
    payload: dict[str, Any],
    reference_alerts: list[dict],
    include_current_event: bool = True,
) -> dict[str, Any]:
    source_counter, tool_counter = _alert_counters(reference_alerts)
    source = str(payload.get("source") or "unknown-source")
    source_tool = str(payload.get("source_tool") or "other")

    return {
        **payload,
        "source": source,
        "source_tool": source_tool,
        "source_frequency": source_counter.get(source, 0) + (1 if include_current_event else 0),
        "source_tool_frequency": tool_counter.get(source_tool, 0) + (1 if include_current_event else 0),
    }


def train_demo_anomaly_model(force_retrain: bool = True) -> dict[str, Any]:
    metadata = (
        anomaly_detector.train_demo_model()
        if force_retrain or not anomaly_detector.is_trained
        else anomaly_detector.get_training_metadata()
    )
    ensure_demo_alerts_scored(force_recompute=True)

    return {
        "model_name": metadata.model_name,
        "trained_on_events": metadata.trained_on_events,
        "feature_labels": metadata.feature_labels,
        "vectorized_feature_count": metadata.vectorized_feature_count,
        "trained_at": metadata.trained_at,
        "message": "IsolationForest retrained on seeded demo SOC events.",
    }


def score_event_payload(
    payload: dict[str, Any],
    *,
    reference_alerts: list[dict] | None = None,
) -> dict[str, Any]:
    context = _build_event_context(payload, reference_alerts or DEMO_ALERTS)
    prediction = anomaly_detector.predict_event(context)

    return {
        "anomaly_score": prediction.anomaly_score,
        "is_anomalous": prediction.is_anomalous,
        "anomaly_explanation": prediction.anomaly_explanation,
        "model_name": prediction.model_name,
    }


def apply_anomaly_scoring(alert_record: dict[str, Any], *, reference_alerts: list[dict] | None = None) -> dict[str, Any]:
    scoring_result = score_event_payload(alert_record, reference_alerts=reference_alerts)
    alert_record["anomaly_score"] = scoring_result["anomaly_score"]
    alert_record["is_anomalous"] = scoring_result["is_anomalous"]
    alert_record["anomaly_explanation"] = scoring_result["anomaly_explanation"]
    return alert_record


def ensure_demo_alerts_scored(force_recompute: bool = False) -> None:
    if not anomaly_detector.is_trained:
        anomaly_detector.train_demo_model()

    for alert_record in DEMO_ALERTS:
        if force_recompute or any(
            field_name not in alert_record
            for field_name in ("anomaly_score", "is_anomalous", "anomaly_explanation")
        ):
            apply_anomaly_scoring(alert_record, reference_alerts=DEMO_ALERTS)


def get_anomaly_summary(limit: int = 5) -> dict[str, Any]:
    ensure_demo_alerts_scored()
    metadata = anomaly_detector.get_training_metadata()
    sorted_alerts = sorted(
        DEMO_ALERTS,
        key=lambda alert: (alert.get("anomaly_score", 0.0), alert.get("created_at")),
        reverse=True,
    )
    anomaly_scores = [float(alert.get("anomaly_score", 0.0)) for alert in DEMO_ALERTS]

    return {
        "model_name": metadata.model_name,
        "trained_on_events": metadata.trained_on_events,
        "feature_labels": metadata.feature_labels,
        "trained_at": metadata.trained_at,
        "average_anomaly_score": round(
            sum(anomaly_scores) / len(anomaly_scores), 2
        )
        if anomaly_scores
        else 0.0,
        "anomalous_alert_count": sum(1 for alert in DEMO_ALERTS if alert.get("is_anomalous")),
        "high_anomaly_alert_count": sum(
            1 for alert in DEMO_ALERTS if float(alert.get("anomaly_score", 0.0)) >= 0.7
        ),
        "top_anomalous_alerts": sorted_alerts[:limit],
    }
