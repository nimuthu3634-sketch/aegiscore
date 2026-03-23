from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "prepare_public_datasets.py"


def test_prepare_unsw_raw_uses_feature_headers_and_balances_categories(tmp_path: Path) -> None:
    features_path = tmp_path / "NUSW-NB15_features.csv"
    features_path.write_text(
        "\n".join(
            [
                "No.,Name,Type,Description",
                "1,srcip,nominal,Source IP address",
                "2,sport,integer,Source port number",
                "3,dstip,nominal,Destination IP address",
            ]
        ),
        encoding="utf-8",
    )
    raw_part_1 = tmp_path / "UNSW-NB15_1.csv"
    raw_part_1.write_text(
        "\n".join(
            [
                "10.0.0.1,80,10.0.0.10,Normal,0",
                "10.0.0.2,443,10.0.0.20,Normal,0",
            ]
        ),
        encoding="utf-8",
    )
    raw_part_2 = tmp_path / "UNSW-NB15_2.csv"
    raw_part_2.write_text("10.0.0.3,53,10.0.0.30,Exploits,1\n", encoding="utf-8")
    output_path = tmp_path / "unsw-prepared.csv"
    summary_path = tmp_path / "unsw-summary.json"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "unsw_nb15",
            "--source",
            "raw",
            "--features",
            str(features_path),
            "--raw-part",
            str(raw_part_1),
            "--raw-part",
            str(raw_part_2),
            "--output",
            str(output_path),
            "--summary-json",
            str(summary_path),
            "--max-rows-per-label",
            "1",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    prepared = pd.read_csv(output_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert list(prepared.columns[:5]) == ["srcip", "sport", "dstip", "attack_cat", "label"]
    assert set(prepared["attack_cat"]) == {"Normal", "Exploits"}
    assert summary["row_count"] == 2
    assert summary["sampling_applied"] is True
    assert summary["label_distribution"] == {"Normal": 1, "Exploits": 1}
    assert summary["source_mode"] == "raw"


def test_prepare_cicids_normalizes_headers_and_adds_binary_labels(tmp_path: Path) -> None:
    monday_path = tmp_path / "Monday-WorkingHours.pcap_ISCX.csv"
    monday_path.write_text(
        "\n".join(
            [
                " Destination Port, Flow Duration, Label",
                "80,10,BENIGN",
                "443,20,DDoS",
            ]
        ),
        encoding="utf-8",
    )
    friday_path = tmp_path / "Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv"
    friday_path.write_text(
        "\n".join(
            [
                " Destination Port, Flow Duration, Label",
                "53,5,PortScan",
                "22,6,PortScan",
            ]
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "cicids-prepared.csv"
    summary_path = tmp_path / "cicids-summary.json"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "cicids2017",
            "--input",
            str(monday_path),
            "--input",
            str(friday_path),
            "--output",
            str(output_path),
            "--summary-json",
            str(summary_path),
            "--max-rows-per-label",
            "1",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    prepared = pd.read_csv(output_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert {"destination_port", "flow_duration", "label", "label_binary", "dataset_family"} <= set(prepared.columns)
    assert summary["row_count"] == 3
    assert summary["sampling_applied"] is True
    assert summary["label_distribution"] == {"BENIGN": 1, "DDoS": 1, "PortScan": 1}
    assert set(prepared["label_binary"]) == {0, 1}
