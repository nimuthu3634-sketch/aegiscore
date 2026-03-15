def get_dashboard_summary() -> dict:
    return {
        "metrics": [
            {"label": "Active Alerts", "value": "128", "note": "Starter mock total"},
            {"label": "Critical Alerts", "value": "09", "note": "High-priority analyst review"},
            {"label": "Open Incidents", "value": "12", "note": "Case workflow placeholder"},
        ],
        "recent_alert_count": 2,
        "recent_incident_count": 2,
    }
