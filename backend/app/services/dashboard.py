def get_dashboard_summary() -> dict:
    return {
        "metrics": [
            {"label": "Active alerts", "value": "128", "change": "+14 today"},
            {"label": "Open incidents", "value": "12", "change": "2 escalated"},
            {"label": "Log events", "value": "48.3K", "change": "Wazuh + Suricata"},
            {"label": "Anomaly score", "value": "0.72", "change": "Model online"},
        ],
        "highlights": [
            "Wazuh and Suricata ingestion pipelines scaffolded.",
            "JWT auth and role separation prepared for implementation.",
            "Anomaly detection placeholder ready for feature engineering.",
        ],
    }
