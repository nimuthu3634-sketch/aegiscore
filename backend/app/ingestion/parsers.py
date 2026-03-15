from collections.abc import Mapping


def parse_wazuh_event(payload: Mapping[str, object]) -> dict[str, object]:
    return {
        "source": "wazuh",
        "normalized_event": dict(payload),
        "parser_status": "placeholder",
    }


def parse_suricata_event(payload: Mapping[str, object]) -> dict[str, object]:
    return {
        "source": "suricata",
        "normalized_event": dict(payload),
        "parser_status": "placeholder",
    }


def parse_lab_import(tool: str, payload: Mapping[str, object]) -> dict[str, object]:
    return {
        "source": tool,
        "normalized_event": dict(payload),
        "parser_status": "lab_only_placeholder",
    }
