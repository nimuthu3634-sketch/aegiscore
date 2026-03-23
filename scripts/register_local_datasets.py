from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "data" / "local_datasets.json"

KNOWN_FILES = {
    "NUSW-NB15_features.csv": {
        "family": "unsw_nb15",
        "role": "feature_reference",
        "display_name": "UNSW-NB15 feature reference",
    },
    "UNSW_NB15_training-set.csv": {
        "family": "unsw_nb15",
        "role": "training_split",
        "display_name": "UNSW-NB15 training split",
    },
    "UNSW_NB15_testing-set.csv": {
        "family": "unsw_nb15",
        "role": "testing_split",
        "display_name": "UNSW-NB15 testing split",
    },
    "UNSW-NB15_1.csv": {
        "family": "unsw_nb15",
        "role": "raw_part_1",
        "display_name": "UNSW-NB15 raw split 1",
    },
    "UNSW-NB15_2.csv": {
        "family": "unsw_nb15",
        "role": "raw_part_2",
        "display_name": "UNSW-NB15 raw split 2",
    },
    "UNSW-NB15_3.csv": {
        "family": "unsw_nb15",
        "role": "raw_part_3",
        "display_name": "UNSW-NB15 raw split 3",
    },
    "UNSW-NB15_4.csv": {
        "family": "unsw_nb15",
        "role": "raw_part_4",
        "display_name": "UNSW-NB15 raw split 4",
    },
    "UNSW-NB15_LIST_EVENTS.csv": {
        "family": "unsw_nb15",
        "role": "event_reference",
        "display_name": "UNSW-NB15 event list",
    },
    "Monday-WorkingHours.pcap_ISCX.csv": {
        "family": "cicids2017",
        "role": "monday_working_hours",
        "display_name": "CICIDS2017 Monday working hours",
    },
    "Tuesday-WorkingHours.pcap_ISCX.csv": {
        "family": "cicids2017",
        "role": "tuesday_working_hours",
        "display_name": "CICIDS2017 Tuesday working hours",
    },
    "Wednesday-workingHours.pcap_ISCX.csv": {
        "family": "cicids2017",
        "role": "wednesday_working_hours",
        "display_name": "CICIDS2017 Wednesday working hours",
    },
    "Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv": {
        "family": "cicids2017",
        "role": "thursday_web_attacks",
        "display_name": "CICIDS2017 Thursday web attacks",
    },
    "Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv": {
        "family": "cicids2017",
        "role": "thursday_infiltration",
        "display_name": "CICIDS2017 Thursday infiltration",
    },
    "Friday-WorkingHours-Morning.pcap_ISCX.csv": {
        "family": "cicids2017",
        "role": "friday_morning",
        "display_name": "CICIDS2017 Friday morning",
    },
    "Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv": {
        "family": "cicids2017",
        "role": "friday_portscan",
        "display_name": "CICIDS2017 Friday afternoon PortScan",
    },
    "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv": {
        "family": "cicids2017",
        "role": "friday_ddos",
        "display_name": "CICIDS2017 Friday afternoon DDoS",
    },
}


def _classify_path(raw_path: str, *, check_exists: bool) -> dict[str, object]:
    path = Path(raw_path)
    metadata = KNOWN_FILES.get(path.name, {})
    return {
        "display_name": metadata.get("display_name", path.stem),
        "family": metadata.get("family", "unclassified"),
        "role": metadata.get("role", "raw_file"),
        "path": raw_path,
        "filename": path.name,
        "extension": path.suffix.lower(),
        "exists": path.exists() if check_exists else None,
    }


def _build_manifest(paths: list[str], *, check_exists: bool) -> dict[str, object]:
    dataset_entries = [_classify_path(path_value, check_exists=check_exists) for path_value in paths]
    family_counts: dict[str, int] = {}
    for entry in dataset_entries:
        family = str(entry["family"])
        family_counts[family] = family_counts.get(family, 0) + 1

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_count": len(dataset_entries),
        "family_counts": family_counts,
        "datasets": dataset_entries,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Register local raw dataset file paths for AegisCore."
    )
    parser.add_argument(
        "--path",
        action="append",
        dest="paths",
        required=True,
        help="Absolute path to a local dataset file. Repeat for each file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Manifest output path. Default: {DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--skip-exists-check",
        action="store_true",
        help="Record paths without checking whether each file is currently reachable.",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    manifest = _build_manifest(args.paths, check_exists=not args.skip_exists_check)
    output_path: Path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(f"{json.dumps(manifest, indent=2)}\n", encoding="utf-8")
    print(f"Registered {manifest['dataset_count']} local dataset file paths -> {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
