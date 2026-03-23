from __future__ import annotations

import csv
import gzip
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "lanl_prepare.py"


def _read_gzip_csv(path: Path) -> list[list[str]]:
    with gzip.open(path, mode="rt", encoding="utf-8", newline="") as handle:
        return [row for row in csv.reader(handle) if row]


def test_prepare_auth_slice_keeps_failures_and_redteam_matches(tmp_path: Path) -> None:
    auth_path = tmp_path / "auth.txt"
    auth_path.write_text(
        "\n".join(
            [
                "930,U24@DOM1,U24@DOM1,C17693,C612,Kerberos,Network,LogOn,Success",
                "931,U24@DOM1,U24@DOM1,C17693,C612,Kerberos,Network,LogOn,Failure",
                "932,U99@DOM1,U99@DOM1,C100,C200,Kerberos,Network,LogOn,Success",
                "933,U24@DOM1,U24@DOM1,C17693,C612,Kerberos,Network,LogOn,Failure",
            ]
        ),
        encoding="utf-8",
    )
    redteam_path = tmp_path / "redteam.txt"
    redteam_path.write_text("930,U24,C17693,C612\n", encoding="utf-8")
    output_path = tmp_path / "auth-alert-candidates.txt.gz"
    summary_path = tmp_path / "auth-summary.json"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "prepare",
            "--dataset-type",
            "auth",
            "--input",
            str(auth_path),
            "--output",
            str(output_path),
            "--redteam-input",
            str(redteam_path),
            "--only-alert-candidates",
            "--summary-json",
            str(summary_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    rows = _read_gzip_csv(output_path)
    assert len(rows) == 3
    assert {row[0] for row in rows} == {"930", "931", "933"}

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["dataset_type"] == "auth"
    assert summary["written_rows"] == 3
    assert summary["filtered_rows"] == 1
    assert summary["redteam_match_count"] == 1


def test_prepare_flow_slice_keeps_sensitive_records_when_requested(tmp_path: Path) -> None:
    flow_path = tmp_path / "flows.txt"
    flow_path.write_text(
        "\n".join(
            [
                "100,30,C10,53124,C20,80,tcp,200,4096",
                "101,45,C10,53125,C30,445,tcp,300,8192",
                "102,60,C10,53126,C40,443,tcp,100,1048576",
            ]
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "flow-alert-candidates.txt.gz"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "prepare",
            "--dataset-type",
            "flows",
            "--input",
            str(flow_path),
            "--output",
            str(output_path),
            "--only-alert-candidates",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    rows = _read_gzip_csv(output_path)
    assert len(rows) == 2
    assert {row[0] for row in rows} == {"101", "102"}
