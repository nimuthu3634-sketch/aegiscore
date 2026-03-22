from app.core.enums import AlertSeverity
from app.ingestion.parsers import parse_lab_import, parse_suricata_event, parse_wazuh_event


def test_parse_wazuh_event_normalizes_file_integrity_alert() -> None:
    parsed = parse_wazuh_event(
        {
            "id": "wazuh-demo-002",
            "timestamp": "2026-03-15T15:42:00Z",
            "agent": {"name": "endpoint-lab-11"},
            "rule": {
                "level": 7,
                "description": "Integrity checksum changed for monitored configuration file",
                "groups": ["syscheck", "configuration"],
            },
            "full_log": "File '/etc/sudoers' checksum changed on monitored endpoint.",
            "syscheck": {"path": "/etc/sudoers", "event": "modified"},
        }
    )

    assert parsed["source"] == "endpoint-lab-11"
    assert parsed["event_type"] == "file_integrity"
    assert parsed["severity"] == AlertSeverity.HIGH
    assert parsed["normalized_event"]["observables"]["path"] == "/etc/sudoers"
    assert parsed["parser_status"] == "normalized"


def test_parse_suricata_event_normalizes_reconnaissance_alert() -> None:
    parsed = parse_suricata_event(
        {
            "timestamp": "2026-03-15T15:21:00Z",
            "event_type": "alert",
            "src_ip": "10.10.30.44",
            "src_port": 51122,
            "dest_ip": "172.16.11.20",
            "dest_port": 3389,
            "proto": "TCP",
            "sensor_name": "sensor-west-01",
            "alert": {
                "signature": "ET SCAN Potential internal RDP reconnaissance activity",
                "category": "Attempted Information Leak",
                "severity": 3,
            },
        }
    )

    assert parsed["source"] == "sensor-west-01"
    assert parsed["event_type"] == "reconnaissance"
    assert parsed["severity"] == AlertSeverity.MEDIUM
    assert parsed["normalized_event"]["observables"]["source_ip"] == "10.10.30.44"
    assert parsed["parser_status"] == "normalized"


def test_parse_nmap_lab_import_marks_lab_only_scan_results() -> None:
    parsed = parse_lab_import(
        "nmap",
        {
            "host": "lab-admin-01",
            "open_ports": [
                {"port": 22, "service_name": "ssh", "protocol": "tcp", "state": "open"},
                {"port": 3389, "service_name": "ms-wbt-server", "protocol": "tcp", "state": "open"},
            ],
            "scan_timestamp": "2026-03-15T08:15:00Z",
        },
    )

    assert parsed["source"] == "lab-admin-01"
    assert parsed["event_type"] == "scan_result"
    assert parsed["severity"] == AlertSeverity.CRITICAL
    assert parsed["lab_only"] is True
    assert parsed["parser_status"] == "normalized"


def test_parse_hydra_lab_import_marks_lab_only_credential_assessment() -> None:
    parsed = parse_lab_import(
        "hydra",
        {
            "target_system": "lab-ssh-01",
            "protocol": "ssh",
            "result_summary": "Authorized classroom credential assessment import recorded a valid credential match for analyst_demo.",
            "timestamp": "2026-03-15T09:05:00Z",
        },
    )

    assert parsed["source"] == "lab-ssh-01"
    assert parsed["event_type"] == "credential_assessment"
    assert parsed["severity"] == AlertSeverity.CRITICAL
    assert parsed["lab_only"] is True
    assert parsed["parser_status"] == "normalized"
