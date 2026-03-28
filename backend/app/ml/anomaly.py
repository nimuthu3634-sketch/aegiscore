from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import exp
import re
from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction import DictVectorizer

from app.utils.log_normalization import normalize_timestamp
from app.utils.time import utc_now

SEVERITY_WEIGHTS = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

LOGIN_KEYWORDS = ("login", "ssh", "rdp", "password", "auth", "credential", "sudo")
NETWORK_KEYWORDS = ("dns", "network", "traffic", "tls", "smb", "packet", "flow")
SERVICE_KEYWORDS = ("port", "service", "exposure", "http", "https", "ssh", "ftp", "postgres", "redis")
CREDENTIAL_KEYWORDS = ("credential", "password", "lockout", "reuse", "match", "brute", "login")


@dataclass
class TrainingMetadata:
    model_name: str
    trained_on_events: int
    feature_labels: list[str]
    vectorized_feature_count: int
    trained_at: datetime


@dataclass
class AnomalyPrediction:
    anomaly_score: float
    is_anomalous: bool
    anomaly_explanation: str
    model_name: str


class DemoAnomalyDetector:
    """A small, explainable anomaly detector for seeded SOC event data."""

    def __init__(self) -> None:
        self.model_name = "IsolationForest"
        self.vectorizer = DictVectorizer(sparse=False)
        self.model = IsolationForest(
            contamination=0.12,
            n_estimators=160,
            random_state=42,
        )
        self.feature_labels = [
            "severity_level",
            "hour_of_day",
            "is_after_hours",
            "source_frequency",
            "source_tool_frequency",
            "open_port_count",
            "max_port_number",
            "unique_service_count",
            "login_keyword_hits",
            "network_keyword_hits",
            "credential_keyword_hits",
            "service_keyword_hits",
            "message_length",
            "source_tool",
            "event_family",
        ]
        self.trained_at: datetime | None = None
        self.training_event_count = 0
        self.vectorized_feature_count = 0
        self.baseline_score_mean = 0.0
        self.baseline_score_std = 1.0
        self.is_trained = False

    def train_demo_model(self, demo_events: list[dict[str, Any]] | None = None) -> TrainingMetadata:
        events = demo_events or self._build_demo_training_events()
        feature_maps = [self._build_feature_map(event) for event in events]
        training_matrix = self.vectorizer.fit_transform(feature_maps)
        self.model.fit(training_matrix)

        training_scores = -self.model.decision_function(training_matrix)
        self.baseline_score_mean = float(np.mean(training_scores))
        self.baseline_score_std = max(float(np.std(training_scores)), 0.08)
        self.trained_at = utc_now()
        self.training_event_count = len(events)
        self.vectorized_feature_count = len(self.vectorizer.get_feature_names_out())
        self.is_trained = True

        return TrainingMetadata(
            model_name=self.model_name,
            trained_on_events=self.training_event_count,
            feature_labels=self.feature_labels,
            vectorized_feature_count=self.vectorized_feature_count,
            trained_at=self.trained_at,
        )

    def predict_event(self, event: dict[str, Any]) -> AnomalyPrediction:
        if not self.is_trained:
            self.train_demo_model()

        feature_map = self._build_feature_map(event)
        event_matrix = self.vectorizer.transform([feature_map])
        raw_score = -float(self.model.decision_function(event_matrix)[0])
        z_score = (raw_score - self.baseline_score_mean) / max(self.baseline_score_std, 1e-6)
        anomaly_score = round(float(np.clip(self._sigmoid(z_score * 1.35), 0.0, 1.0)), 2)
        is_anomalous = bool(anomaly_score >= 0.6 or int(self.model.predict(event_matrix)[0]) == -1)

        return AnomalyPrediction(
            anomaly_score=anomaly_score,
            is_anomalous=is_anomalous,
            anomaly_explanation=self._build_explanation(event, feature_map, anomaly_score),
            model_name=self.model_name,
        )

    def get_training_metadata(self) -> TrainingMetadata:
        if not self.is_trained:
            return self.train_demo_model()

        return TrainingMetadata(
            model_name=self.model_name,
            trained_on_events=self.training_event_count,
            feature_labels=self.feature_labels,
            vectorized_feature_count=self.vectorized_feature_count,
            trained_at=self.trained_at or utc_now(),
        )

    def _sigmoid(self, value: float) -> float:
        return 1 / (1 + exp(-value))

    def _build_demo_training_events(self) -> list[dict[str, Any]]:
        rng = np.random.default_rng(42)
        templates = [
            {
                "source_tool": "wazuh",
                "event_family": "authentication",
                "text": "baseline user login activity on classroom endpoint",
                "severity": "low",
                "source_prefix": "endpoint-lab-",
                "port_options": [22],
            },
            {
                "source_tool": "suricata",
                "event_family": "network",
                "text": "baseline outbound web traffic from classroom workstation",
                "severity": "medium",
                "source_prefix": "sensor-",
                "port_options": [53, 80, 443],
            },
            {
                "source_tool": "nmap",
                "event_family": "scan_result",
                "text": "authorized lab scan baseline import with expected services",
                "severity": "low",
                "source_prefix": "lab-web-",
                "port_options": [22, 80, 443],
            },
            {
                "source_tool": "hydra",
                "event_family": "credential_assessment",
                "text": "authorized credential assessment import with routine failed attempts",
                "severity": "medium",
                "source_prefix": "lab-cred-",
                "port_options": [],
            },
        ]

        demo_events: list[dict[str, Any]] = []
        for index in range(180):
            template = templates[index % len(templates)]
            hour_value = int(rng.integers(8, 19))
            source_suffix = int(rng.integers(1, 7))
            chosen_ports = template["port_options"][: int(rng.integers(0, len(template["port_options"]) + 1))]
            demo_events.append(
                {
                    "title": template["text"].title(),
                    "description": template["text"],
                    "source": f"{template['source_prefix']}{source_suffix:02d}",
                    "source_tool": template["source_tool"],
                    "severity": template["severity"],
                    "created_at": datetime(2026, 3, 10, hour_value, int(rng.integers(0, 60))),
                    "event_type": template["event_family"],
                    "source_frequency": int(rng.integers(1, 3)),
                    "source_tool_frequency": int(rng.integers(1, 4)),
                    "finding_metadata": {
                        "open_ports": [
                            {"port": port_value, "service_name": "baseline-service"}
                            for port_value in chosen_ports
                        ],
                        "service_names": ["baseline-service"] if chosen_ports else [],
                    },
                }
            )

        return demo_events

    def _build_feature_map(self, event: dict[str, Any]) -> dict[str, Any]:
        timestamp = normalize_timestamp(event.get("created_at") or event.get("timestamp"))
        combined_text = self._combined_text(event)
        port_numbers = self._extract_port_numbers(event)
        service_names = self._extract_service_names(event)
        source_tool = str(event.get("source_tool") or "other").lower()
        event_family = str(event.get("event_type") or self._infer_event_family(combined_text)).lower()

        return {
            "source_tool": source_tool,
            "event_family": event_family,
            "severity_level": self._severity_weight(event.get("severity")),
            "hour_of_day": timestamp.hour,
            "is_after_hours": int(timestamp.hour < 7 or timestamp.hour > 19),
            "source_frequency": int(event.get("source_frequency") or 1),
            "source_tool_frequency": int(event.get("source_tool_frequency") or 1),
            "open_port_count": len(port_numbers),
            "max_port_number": max(port_numbers) if port_numbers else 0,
            "unique_service_count": len(service_names),
            "login_keyword_hits": self._keyword_hits(combined_text, LOGIN_KEYWORDS),
            "network_keyword_hits": self._keyword_hits(combined_text, NETWORK_KEYWORDS),
            "credential_keyword_hits": self._keyword_hits(combined_text, CREDENTIAL_KEYWORDS),
            "service_keyword_hits": self._keyword_hits(combined_text, SERVICE_KEYWORDS),
            "message_length": min(len(combined_text), 320),
        }

    def _severity_weight(self, severity_value: Any) -> int:
        return SEVERITY_WEIGHTS.get(str(severity_value or "low").lower(), 1)

    def _combined_text(self, event: dict[str, Any]) -> str:
        parts = [
            str(event.get("title") or ""),
            str(event.get("description") or ""),
            str(event.get("event_type") or ""),
            str(event.get("source") or ""),
        ]

        finding_metadata = event.get("finding_metadata") or {}
        if isinstance(finding_metadata, dict):
            parts.extend(
                [
                    " ".join(str(item) for item in finding_metadata.get("service_names", [])),
                    str(finding_metadata.get("result_summary") or ""),
                    str(finding_metadata.get("scan_notes") or ""),
                ]
            )

        normalized_log = event.get("normalized_log") or {}
        if isinstance(normalized_log, dict):
            parts.append(str(normalized_log.get("message") or ""))
            parts.append(str(normalized_log.get("event_type") or ""))

        raw_log = event.get("raw_log") or {}
        if isinstance(raw_log, dict):
            parts.append(str(raw_log.get("message") or raw_log.get("summary") or ""))

        return " ".join(part for part in parts if part).lower()

    def _extract_port_numbers(self, event: dict[str, Any]) -> list[int]:
        port_numbers: list[int] = []
        finding_metadata = event.get("finding_metadata") or {}

        open_ports = finding_metadata.get("open_ports", []) if isinstance(finding_metadata, dict) else []
        for port_record in open_ports:
            if isinstance(port_record, dict):
                port_value = port_record.get("port")
            else:
                port_value = port_record

            try:
                port_numbers.append(int(port_value))
            except (TypeError, ValueError):
                continue

        if port_numbers:
            return port_numbers

        raw_log = event.get("raw_log") or {}
        if isinstance(raw_log, dict):
            candidate_values = [
                raw_log.get("port"),
                raw_log.get("dest_port"),
                raw_log.get("dport"),
            ]
            for candidate in candidate_values:
                try:
                    port_numbers.append(int(candidate))
                except (TypeError, ValueError):
                    continue

        if port_numbers:
            return port_numbers

        return [int(match) for match in re.findall(r"\b(\d{2,5})\b", self._combined_text(event))[:3]]

    def _extract_service_names(self, event: dict[str, Any]) -> set[str]:
        service_names: set[str] = set()
        finding_metadata = event.get("finding_metadata") or {}
        if isinstance(finding_metadata, dict):
            for service_name in finding_metadata.get("service_names", []):
                if str(service_name).strip():
                    service_names.add(str(service_name).strip().lower())

            for port_record in finding_metadata.get("open_ports", []):
                if isinstance(port_record, dict) and str(port_record.get("service_name") or "").strip():
                    service_names.add(str(port_record["service_name"]).strip().lower())

        return service_names

    def _infer_event_family(self, combined_text: str) -> str:
        if self._keyword_hits(combined_text, LOGIN_KEYWORDS) >= 2:
            return "authentication"
        if self._keyword_hits(combined_text, CREDENTIAL_KEYWORDS) >= 2:
            return "credential_assessment"
        if self._keyword_hits(combined_text, SERVICE_KEYWORDS) >= 2:
            return "scan_result"
        if self._keyword_hits(combined_text, NETWORK_KEYWORDS) >= 2:
            return "network"
        return "other"

    def _keyword_hits(self, combined_text: str, keywords: tuple[str, ...]) -> int:
        return sum(1 for keyword in keywords if keyword in combined_text)

    def _build_explanation(
        self,
        event: dict[str, Any],
        feature_map: dict[str, Any],
        anomaly_score: float,
    ) -> str:
        if anomaly_score < 0.55:
            return "within the learned demo baseline"

        if feature_map["login_keyword_hits"] >= 2 and (
            feature_map["source_frequency"] >= 2 or feature_map["severity_level"] >= 3
        ):
            return "unusual login volume"

        if feature_map["credential_keyword_hits"] >= 2 and feature_map["severity_level"] >= 3:
            return "credential activity outside baseline"

        if feature_map["source_frequency"] >= 3 or feature_map["source_tool_frequency"] >= 6:
            return "abnormal source frequency"

        if (
            feature_map["open_port_count"] >= 3
            or feature_map["max_port_number"] >= 1024
            or feature_map["service_keyword_hits"] >= 2
        ):
            return "unusual service/port activity"

        if feature_map["is_after_hours"] and feature_map["severity_level"] >= 3:
            return "after-hours activity outside baseline"

        if anomaly_score >= 0.6:
            return "combined anomaly pattern across severity and source activity"

        return "combined anomaly pattern across severity and source activity"


anomaly_detector = DemoAnomalyDetector()
