from __future__ import annotations

import argparse
import csv
import gzip
import json
import shutil
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ingestion.parsers import (  # noqa: E402
    LANL_FAILURE_VALUES,
    parse_lanl_auth_record,
    parse_lanl_dns_record,
    parse_lanl_flow_record,
)

DATA_ROOT = REPO_ROOT / "data" / "lanl"
RAW_DATA_DIR = DATA_ROOT / "raw"
PREPARED_DATA_DIR = DATA_ROOT / "prepared"
DOWNLOAD_FILENAMES = {
    "auth": "auth.txt.gz",
    "dns": "dns.txt.gz",
    "flows": "flows.txt.gz",
    "redteam": "redteam.txt.gz",
}


def _open_text_reader(path: Path):
    with path.open("rb") as file_handle:
        header = file_handle.read(2)

    if header == b"\x1f\x8b" or path.suffix.lower() == ".gz":
        return None, gzip.open(path, mode="rt", encoding="utf-8", newline="")

    return None, path.open("rt", encoding="utf-8", newline="")


def _open_text_writer(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".gz":
        return gzip.open(path, mode="wt", encoding="utf-8", newline="")
    return path.open("wt", encoding="utf-8", newline="")


def _normalize_cells(row: list[str]) -> list[str]:
    return [cell.strip() for cell in row]


def _read_redteam_matches(path: Path | None) -> set[tuple[str, str, str, str]]:
    if path is None:
        return set()

    compression_handle, text_stream = _open_text_reader(path)
    matches: set[tuple[str, str, str, str]] = set()

    try:
        for row in csv.reader(text_stream):
            if len(row) < 4:
                continue

            relative_time = row[0].strip()
            username = row[1].strip().lower()
            username_short = username.split("@", 1)[0]
            source_computer = row[2].strip().lower()
            destination_computer = row[3].strip().lower()

            matches.add((relative_time, username, source_computer, destination_computer))
            matches.add((relative_time, username_short, source_computer, destination_computer))
    finally:
        text_stream.close()
        if compression_handle is not None:
            compression_handle.close()

    return matches


def _is_redteam_auth_match(row: list[str], redteam_matches: set[tuple[str, str, str, str]]) -> bool:
    if len(row) < 5:
        return False

    relative_time = row[0].strip()
    username = row[1].strip().lower()
    username_short = username.split("@", 1)[0]
    source_computer = row[3].strip().lower()
    destination_computer = row[4].strip().lower()

    return (
        (relative_time, username, source_computer, destination_computer) in redteam_matches
        or (relative_time, username_short, source_computer, destination_computer) in redteam_matches
    )


def _parse_redteam_row(row: list[str]) -> dict[str, Any]:
    if len(row) < 4:
        raise ValueError("LANL red-team records must contain 4 columns.")

    relative_time_seconds = int(row[0].strip())
    return {
        "finding_metadata": {
            "dataset_type": "redteam",
            "relative_time_seconds": relative_time_seconds,
            "source_user": row[1].strip(),
            "source_computer": row[2].strip(),
            "destination_computer": row[3].strip(),
        }
    }


def _parse_lanl_row(
    dataset_type: str,
    row: list[str],
    *,
    redteam_matches: set[tuple[str, str, str, str]],
) -> dict[str, Any]:
    if dataset_type == "auth":
        return parse_lanl_auth_record(row, redteam_match=_is_redteam_auth_match(row, redteam_matches))
    if dataset_type == "dns":
        return parse_lanl_dns_record(row)
    if dataset_type == "flows":
        return parse_lanl_flow_record(row)
    return _parse_redteam_row(row)


def _is_alert_candidate(dataset_type: str, parsed_record: dict[str, Any]) -> bool:
    metadata = parsed_record.get("finding_metadata", {})

    if dataset_type == "auth":
        auth_outcome = str(metadata.get("auth_outcome") or "").strip().lower()
        return bool(metadata.get("redteam_match")) or auth_outcome in LANL_FAILURE_VALUES

    if dataset_type == "flows":
        return (
            bool(metadata.get("sensitive_port_match"))
            or int(metadata.get("byte_count") or 0) >= 1_000_000
            or int(metadata.get("duration_seconds") or 0) >= 1800
        )

    return True


def _default_download_path(
    *,
    url: str,
    dataset_type: str | None,
    output: Path | None,
    output_dir: Path,
) -> Path:
    if output is not None:
        return output

    parsed = urlparse(url)
    filename = Path(parsed.path).name

    if not filename and dataset_type:
        filename = DOWNLOAD_FILENAMES[dataset_type]
    if not filename:
        raise ValueError("Could not determine the download filename. Pass --output explicitly.")

    return output_dir / filename


def download_lanl_file(
    *,
    url: str,
    dataset_type: str | None,
    output: Path | None,
    output_dir: Path,
    skip_if_exists: bool,
) -> dict[str, Any]:
    destination = _default_download_path(
        url=url,
        dataset_type=dataset_type,
        output=output,
        output_dir=output_dir,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)

    if skip_if_exists and destination.exists():
        return {
            "output_path": str(destination),
            "bytes_written": destination.stat().st_size,
            "skipped": True,
        }

    request = Request(
        url,
        headers={
            "User-Agent": "AegisCore-LANL-Prep/1.0",
        },
    )

    try:
        with urlopen(request) as response, destination.open("wb") as output_handle:
            shutil.copyfileobj(response, output_handle)
    except HTTPError as exc:
        raise RuntimeError(
            "LANL download failed. Use a direct official file URL from the LANL dataset page."
        ) from exc
    except URLError as exc:
        raise RuntimeError("LANL download failed because the URL could not be reached.") from exc

    return {
        "output_path": str(destination),
        "bytes_written": destination.stat().st_size,
        "skipped": False,
    }


def _default_prepared_path(
    *,
    dataset_type: str,
    output: Path | None,
    output_dir: Path,
    max_records: int,
    skip_records: int,
    only_alert_candidates: bool,
) -> Path:
    if output is not None:
        return output

    selection_label = "alert-candidates" if only_alert_candidates else "first"
    if skip_records > 0:
        selection_label = f"{selection_label}-after-{skip_records}"

    return output_dir / f"{dataset_type}-{selection_label}-{max_records}.txt.gz"


def prepare_lanl_slice(
    *,
    dataset_type: str,
    input_path: Path,
    output: Path | None,
    output_dir: Path,
    max_records: int,
    skip_records: int,
    only_alert_candidates: bool,
    redteam_input: Path | None,
    summary_json: Path | None,
) -> dict[str, Any]:
    if max_records < 1:
        raise ValueError("max_records must be at least 1.")
    if skip_records < 0:
        raise ValueError("skip_records cannot be negative.")
    if not input_path.exists():
        raise FileNotFoundError(f"LANL input file was not found: {input_path}")
    if dataset_type != "auth" and redteam_input is not None:
        raise ValueError("redteam_input can only be used with the auth dataset type.")

    output_path = _default_prepared_path(
        dataset_type=dataset_type,
        output=output,
        output_dir=output_dir,
        max_records=max_records,
        skip_records=skip_records,
        only_alert_candidates=only_alert_candidates,
    )

    redteam_matches = _read_redteam_matches(redteam_input) if redteam_input else set()
    compression_handle, text_stream = _open_text_reader(input_path)
    rows_scanned = 0
    valid_rows = 0
    candidate_rows = 0
    written_rows = 0
    invalid_rows = 0
    filtered_rows = 0
    skipped_rows = 0
    redteam_match_count = 0
    first_relative_time: int | None = None
    last_relative_time: int | None = None

    try:
        with _open_text_writer(output_path) as output_stream:
            writer = csv.writer(output_stream, lineterminator="\n")

            for row in csv.reader(text_stream):
                if not row or not any(cell.strip() for cell in row):
                    continue

                rows_scanned += 1
                cleaned_row = _normalize_cells(row)

                try:
                    parsed_record = _parse_lanl_row(
                        dataset_type,
                        cleaned_row,
                        redteam_matches=redteam_matches,
                    )
                except (TypeError, ValueError):
                    invalid_rows += 1
                    continue

                valid_rows += 1

                if only_alert_candidates and not _is_alert_candidate(dataset_type, parsed_record):
                    filtered_rows += 1
                    continue

                candidate_rows += 1
                if candidate_rows <= skip_records:
                    skipped_rows += 1
                    continue

                writer.writerow(cleaned_row)
                written_rows += 1

                metadata = parsed_record.get("finding_metadata", {})
                relative_time = int(metadata.get("relative_time_seconds") or 0)
                first_relative_time = (
                    relative_time if first_relative_time is None else min(first_relative_time, relative_time)
                )
                last_relative_time = (
                    relative_time if last_relative_time is None else max(last_relative_time, relative_time)
                )

                if dataset_type == "auth" and bool(metadata.get("redteam_match")):
                    redteam_match_count += 1

                if written_rows >= max_records:
                    break
    finally:
        text_stream.close()
        if compression_handle is not None:
            compression_handle.close()

    summary = {
        "dataset_type": dataset_type,
        "input_path": str(input_path),
        "output_path": str(output_path),
        "selection_mode": "alert_candidates" if only_alert_candidates else "all_rows",
        "rows_scanned": rows_scanned,
        "valid_rows": valid_rows,
        "candidate_rows": candidate_rows,
        "written_rows": written_rows,
        "invalid_rows": invalid_rows,
        "filtered_rows": filtered_rows,
        "skipped_rows": skipped_rows,
        "redteam_match_count": redteam_match_count,
        "first_relative_time_seconds": first_relative_time,
        "last_relative_time_seconds": last_relative_time,
    }

    if summary_json is not None:
        summary_json.parent.mkdir(parents=True, exist_ok=True)
        summary_json.write_text(f"{json.dumps(summary, indent=2)}\n", encoding="utf-8")
        summary["summary_json"] = str(summary_json)

    return summary


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Download official LANL Comprehensive dataset files and prepare smaller upload-friendly slices "
            "for the AegisCore web app."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    download_parser = subparsers.add_parser(
        "download",
        help="Download a LANL file from a direct official URL into a local ignored folder.",
    )
    download_parser.add_argument("--url", required=True, help="Direct official LANL file URL.")
    download_parser.add_argument(
        "--dataset-type",
        choices=sorted(DOWNLOAD_FILENAMES),
        help="Optional dataset type to help pick a default filename.",
    )
    download_parser.add_argument("--output", type=Path, help="Optional exact output path.")
    download_parser.add_argument(
        "--output-dir",
        type=Path,
        default=RAW_DATA_DIR,
        help=f"Directory for downloaded LANL files. Default: {RAW_DATA_DIR}",
    )
    download_parser.add_argument(
        "--skip-if-exists",
        action="store_true",
        help="Leave an existing downloaded file in place instead of downloading again.",
    )

    prepare_parser = subparsers.add_parser(
        "prepare",
        help="Validate and slice a smaller LANL subset that uploads cleanly into AegisCore.",
    )
    prepare_parser.add_argument(
        "--dataset-type",
        required=True,
        choices=["auth", "dns", "flows", "redteam"],
        help="Which LANL file format is being prepared.",
    )
    prepare_parser.add_argument("--input", type=Path, required=True, help="Path to the LANL input file.")
    prepare_parser.add_argument("--output", type=Path, help="Optional exact output path.")
    prepare_parser.add_argument(
        "--output-dir",
        type=Path,
        default=PREPARED_DATA_DIR,
        help=f"Directory for prepared LANL slices. Default: {PREPARED_DATA_DIR}",
    )
    prepare_parser.add_argument(
        "--max-records",
        type=int,
        default=1000,
        help="Maximum number of valid rows to write to the prepared output.",
    )
    prepare_parser.add_argument(
        "--skip-records",
        type=int,
        default=0,
        help="Number of selected rows to skip before writing output rows.",
    )
    prepare_parser.add_argument(
        "--only-alert-candidates",
        action="store_true",
        help=(
            "Keep only rows that are likely to create useful alerts in AegisCore. "
            "For auth this keeps failures and red-team matches; for flows it keeps sensitive/high-volume records."
        ),
    )
    prepare_parser.add_argument(
        "--redteam-input",
        type=Path,
        help="Optional redteam.txt(.gz) file used to preserve LANL auth ground-truth matches.",
    )
    prepare_parser.add_argument(
        "--summary-json",
        type=Path,
        help="Optional path to write a JSON summary for the prepared slice.",
    )

    return parser


def _run_download(args: argparse.Namespace) -> int:
    result = download_lanl_file(
        url=args.url,
        dataset_type=args.dataset_type,
        output=args.output,
        output_dir=args.output_dir,
        skip_if_exists=args.skip_if_exists,
    )
    status_prefix = "Reused" if result["skipped"] else "Downloaded"
    print(f"{status_prefix} LANL file -> {result['output_path']}")
    print(f"Bytes available: {result['bytes_written']}")
    return 0


def _run_prepare(args: argparse.Namespace) -> int:
    summary = prepare_lanl_slice(
        dataset_type=args.dataset_type,
        input_path=args.input,
        output=args.output,
        output_dir=args.output_dir,
        max_records=args.max_records,
        skip_records=args.skip_records,
        only_alert_candidates=args.only_alert_candidates,
        redteam_input=args.redteam_input,
        summary_json=args.summary_json,
    )
    print(f"Prepared LANL {summary['dataset_type']} slice -> {summary['output_path']}")
    print(
        "Rows written: "
        f"{summary['written_rows']} "
        f"(scanned {summary['rows_scanned']}, invalid {summary['invalid_rows']}, filtered {summary['filtered_rows']})"
    )
    if "summary_json" in summary:
        print(f"Summary JSON: {summary['summary_json']}")
    return 0


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        if args.command == "download":
            return _run_download(args)
        return _run_prepare(args)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        parser.exit(1, f"Error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
